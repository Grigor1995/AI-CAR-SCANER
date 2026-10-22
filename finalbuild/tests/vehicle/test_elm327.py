import pytest
from vehicle.obd.protocols.elm327 import ELM327Protocol, OBDProtocolError

def test_rpm_decode(): assert ELM327Protocol.rpm(bytes([0x0B,0xB8])) == 750.0

def test_coolant_decode(): assert ELM327Protocol.coolant_c(bytes([90])) == 50.0

def test_dtc_decode(): assert ELM327Protocol.dtc_codes(bytes.fromhex('43 03 02 00 00')) == ['P0302']

def test_no_data():
    with pytest.raises(OBDProtocolError): ELM327Protocol.parse_hex_payload('010C','NO DATA')


@pytest.mark.parametrize("frame", [
    "410C0BB8",
    "41 0C 0B B8",
    "7E8 04 41 0C 0B B8",
    "010C\r410C0BB8\r>",
    "18DAF110 04 41 0C 0B B8",
])
def test_real_elm327_ats0_compact_pid_and_can_header(frame):
    assert ELM327Protocol.rpm(ELM327Protocol.parse_pid(0x0C, frame)) == 750.0


def test_real_elm327_unspaced_dtc_and_vin_service_headers():
    dtc = ELM327Protocol.parse_hex_payload("03", "4303020000")
    assert ELM327Protocol.dtc_codes(dtc.payload) == ["P0302"]
    response = ELM327Protocol.parse_hex_payload("0902", "490201" + "574442")
    assert response.payload[:3] == bytes.fromhex("49 02 01")


def test_negative_service_reply_must_not_be_used_as_valid_pid_data():
    with pytest.raises(OBDProtocolError):
        ELM327Protocol.parse_pid(0x0C, "7F0111")


def test_elm_hex_parser_rejects_unrelated_service_reply():
    with pytest.raises(OBDProtocolError):
        ELM327Protocol.parse_hex_payload("010C", "410500")
