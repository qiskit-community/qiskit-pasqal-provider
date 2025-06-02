"""Testing device and target objects"""

from dataclasses import replace

import pytest
from pulser.devices import Device, AnalogDevice

from qiskit_pasqal_provider.providers.target import (
    PasqalTarget,
)
from qiskit_pasqal_provider.providers.layouts import (
    SquareLayout,
)


def test_target_with_device_types(
    pasqal_device: Device,
    hybrid_device: Device,
    square_layout1: SquareLayout,
) -> None:
    """Test PasqalTarget with different device types"""

    # pasqal_device must pass since it has calibrated_layouts defined
    assert PasqalTarget(pasqal_device, None)

    # pasqal_device should fail if trying to put a layout that is not in the list
    with pytest.raises(ValueError):
        PasqalTarget(pasqal_device, square_layout1)

    # hybrid_device with no layout must fail
    with pytest.raises(ValueError):
        PasqalTarget(hybrid_device, None)

    assert PasqalTarget(hybrid_device, square_layout1)


def test_target_with_custom_device(square_layout1: SquareLayout) -> None:
    """Test PasqalTarget with custom device and layout"""
    mock_device = replace(
        AnalogDevice,
        name="ExampleDevice",
        dimensions=2,
        rydberg_level=61,
        accepts_new_layouts=True,
        pre_calibrated_layouts=(),
    )

    # no layout, should fail
    with pytest.raises(ValueError):
        PasqalTarget(mock_device, None)

    # define layout, should pass
    assert PasqalTarget(mock_device, square_layout1)
