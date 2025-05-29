"""Testing device and target objects"""

from dataclasses import replace

import pytest
from pulser.devices import Device, VirtualDevice
from pulser.channels import Rydberg, Raman

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
    virtual_device = VirtualDevice(
        name="MockVirtualDevice",
        dimensions=2,
        rydberg_level=61,
    )
    virtual_device = replace(
        virtual_device,
        channel_ids=(
            "ryd_loc",
            "ram_loc",
        ),
        channel_objects=(
            Rydberg.Local(None, None, max_duration=None),
            Raman.Local(None, None, max_duration=None),
        ),
    )

    # no layout, should fail
    with pytest.raises(ValueError):
        PasqalTarget(virtual_device, None)  # type: ignore [arg-type]

    # define layout, should pass
    assert PasqalTarget(virtual_device, square_layout1)  # type: ignore [arg-type]
