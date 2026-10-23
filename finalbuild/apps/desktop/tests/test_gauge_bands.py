"""Visual temperature references stay equivalent across display units."""
import pytest
from apps.desktop.demo_ui import AnalogGauge
from PySide6.QtWidgets import QApplication


@pytest.fixture
def qapp():
    return QApplication.instance() or QApplication([])


def test_coolant_reference_and_fahrenheit(qapp):
    gauge = AnalogGauge('#ffffff')
    gauge.channel = '0x05'
    gauge.unit = '°C'
    assert gauge.bands()[2][:2] == (92, 102)
    for value in (92, 97, 102):
        gauge.value = value
        assert gauge.value_color() == '#35CF87'
    gauge.unit = '°F'
    assert gauge.bands()[2][:2] == pytest.approx((197.6, 215.6))
    gauge.value = 206.6
    assert gauge.value_color() == '#35CF87'


def test_intake_temperature_does_not_use_coolant_reference(qapp):
    gauge = AnalogGauge('#ffffff')
    gauge.channel = 'Intake air temperature'
    gauge.unit = '°C'
    assert gauge.bands()[2][:2] != (92, 102)
    bands = gauge.bands()
    assert bands[0][0] == gauge.scale()[0]
    assert bands[-1][1] == gauge.scale()[1]
    assert all(left[1] == right[0] for left, right in zip(bands, bands[1:]))
