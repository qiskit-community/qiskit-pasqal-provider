import pytest

from pulser import Register as PasqalRegister, AnalogDevice as PasqalAnalogDevice
from pulser.devices import Device as PasqalDevice


@pytest.fixture
def pasqal_register() -> PasqalRegister:
    return PasqalRegister.rectangle(1, 4, spacing=5, prefix="atom")


@pytest.fixture
def pasqal_device() -> PasqalDevice:
    return PasqalAnalogDevice
