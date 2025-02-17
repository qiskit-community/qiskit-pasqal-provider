"""fixture for tests."""

import pytest

from pulser import Register as PasqalRegister
from pulser.devices import Device

from qiskit_pasqal_provider.providers.layouts import (
    SquareLayout,
)
from qiskit_pasqal_provider.providers.target import (
    PasqalDevice,
    AVAILABLE_DEVICES,
    PasqalTarget,
)


@pytest.fixture
def pasqal_target() -> PasqalTarget:
    """
    fixture for pre-defined pasqal target instance.
    """
    return PasqalTarget(device=AVAILABLE_DEVICES["pasqal_device"])


@pytest.fixture
def pasqal_register() -> PasqalRegister:
    """
    fixture for rectangle-shaped Pasqal Register instance.
    """
    return PasqalRegister.rectangle(1, 4, spacing=5, prefix="atom")


@pytest.fixture
def pasqal_device() -> PasqalDevice | Device:
    """
    fixture for pulser.devices.AnalogDevice object.
    """
    return AVAILABLE_DEVICES["pasqal_device"]


@pytest.fixture
def hybrid_device() -> PasqalDevice | Device:
    """
    fixture for pulser.devices.AnalogDevice object.
    """
    return AVAILABLE_DEVICES["hybrid"]


@pytest.fixture
def square_layout1() -> SquareLayout:
    """
    fixture for pulser square layout instance.
    """
    return SquareLayout(7, 4, spacing=5)
