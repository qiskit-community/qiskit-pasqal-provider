"""Testing device and target objects"""

from dataclasses import replace

import pytest
from pulser.devices import Device, AnalogDevice
from pulser.register import Register

from qiskit_pasqal_provider.providers.pulse_utils import place_register
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


def test_target_accepts_calibrated_layout_on_closed_device(
    pasqal_device: Device, square_layout1: SquareLayout
) -> None:
    """Test PasqalTarget with a device that only accepts calibrated layouts"""
    closed_device = replace(pasqal_device, accepts_new_layouts=False)
    calibrated_layout = closed_device.pre_calibrated_layouts[0]

    assert PasqalTarget(closed_device, calibrated_layout).layout == calibrated_layout

    with pytest.raises(ValueError):
        PasqalTarget(closed_device, square_layout1)


def test_place_register_without_required_layout(pasqal_device: Device) -> None:
    """Test place_register leaves the register untouched if no layout is required"""
    register = Register.from_coordinates([(0, 0), (5, 0)], prefix="q")
    device = replace(pasqal_device, requires_layout=False)

    assert place_register(register, device) is register


def test_place_register_on_calibrated_layout(pasqal_device: Device) -> None:
    """Test place_register maps atoms onto the device's calibrated layout"""
    calibrated_layout = pasqal_device.pre_calibrated_layouts[0]
    coords = calibrated_layout.define_register(0, 1, 2).qubits.values()
    register = Register.from_coordinates(list(coords), prefix="q")

    placed = place_register(register, pasqal_device)

    assert placed.layout == calibrated_layout
    assert placed.qubit_ids == register.qubit_ids
    pasqal_device.validate_register(placed)


def test_place_register_on_given_layout(
    hybrid_device: Device, square_layout1: SquareLayout
) -> None:
    """Test place_register maps atoms onto a user-given layout"""
    coords = square_layout1.define_register(0, 1, 4).qubits.values()
    register = Register.from_coordinates(list(coords), prefix="q")

    placed = place_register(register, hybrid_device, square_layout1)

    assert placed.layout == square_layout1
    assert placed.qubit_ids == register.qubit_ids


def test_place_register_generates_layout(pasqal_device: Device) -> None:
    """Test place_register generates a layout when atoms are off the given traps"""
    register = Register.from_coordinates([(0, 0), (7, 1), (1, 9)], prefix="q")

    placed = place_register(register, pasqal_device)

    assert placed.layout is not None
    assert not pasqal_device.is_calibrated_layout(placed.layout)
    assert placed.qubit_ids == register.qubit_ids


def test_place_register_rejects_new_layout(pasqal_device: Device) -> None:
    """Test place_register fails when atoms are off traps and new layouts are not accepted"""
    register = Register.from_coordinates([(0, 0), (7, 1), (1, 9)], prefix="q")
    closed_device = replace(pasqal_device, accepts_new_layouts=False)

    with pytest.raises(ValueError):
        place_register(register, closed_device)
