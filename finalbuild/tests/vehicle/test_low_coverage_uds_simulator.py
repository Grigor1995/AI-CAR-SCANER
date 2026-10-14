from vehicle.adapters.can_simulator import SimulatedCanBus
from vehicle.adapters.uds_simulator import UdsEcuSimulator
from vehicle.can.models import CanFrame


def test_uds_simulator_positive_negative_and_unsupported_services():
    bus = SimulatedCanBus()
    ecu = UdsEcuSimulator(
        bus, vin="VIN12345678901234", software_version="SW-9", hardware_version="HW-8",
        dtc_records=[(0x030200, 0x28), (0x010203, 0x01)],
    )

    assert ecu._response_payload(0x10, b"\x03") == b"\x50\x03"
    vin = ecu._response_payload(0x22, b"\xF1\x90")
    assert vin == b"\x62\xF1\x90VIN12345678901234"
    assert ecu._response_payload(0x22, b"\xF1\x99") == b"\x7F\x22\x31"
    dtcs = ecu._response_payload(0x19, b"\x02")
    assert dtcs[:4] == b"\x59\x02\xFF"
    assert len(dtcs) == 4 + 8
    assert ecu._response_payload(0x19, b"\x01") == b"\x7F\x19\x12"
    assert ecu._response_payload(0x11, b"") == b"\x7F\x11\x11"


def test_uds_simulator_handles_ignored_frames_and_releases_multiframe_response():
    bus = SimulatedCanBus()
    ecu = UdsEcuSimulator(bus, request_id=0x7E0, response_id=0x7E8, vin="VIN12345678901234")

    # Different arbitration ID and empty ISO-TP single frame are ignored.
    import asyncio
    asyncio.run(ecu.on_tx(CanFrame(0x7E1, b"\x02\x10\x03")))
    asyncio.run(ecu.on_tx(CanFrame(0x7E0, b"\x00")))
    assert not bus.rx

    # VIN read is larger than a single CAN frame; the simulator queues
    # consecutive frames until the client grants flow control.
    asyncio.run(ecu.on_tx(CanFrame(0x7E0, b"\x03\x22\xF1\x90")))
    assert len(bus.rx) == 1
    assert bus.rx[0].data[0] >> 4 == 1
    assert ecu._pending_cf

    asyncio.run(ecu.on_tx(CanFrame(0x7E0, b"\x30\x00\x00")))
    assert not ecu._pending_cf
    assert len(bus.rx) == 3
    assert all(frame.arbitration_id == 0x7E8 for frame in bus.rx)
    assert bus.rx[1].data[0] >> 4 == 2
