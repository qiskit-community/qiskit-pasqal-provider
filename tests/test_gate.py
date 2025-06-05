"""Testing `HamiltonianGate` and `InterpolatePoints` classes."""

import pytest

import numpy as np
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.circuit.exceptions import CircuitError

from qiskit_pasqal_provider.providers.pulse_utils import (
    PasqalRegister,
    InterpolatePoints,
)
from qiskit_pasqal_provider.providers.gate import HamiltonianGate
from tests.conftest import null_interpolate_points


def test_interpolate_points() -> None:
    """testing `InterpolatePoints` class correctness."""

    p = Parameter("p")
    t = Parameter("t")
    values = [0, 1 / 3 * p, 2 / 3 * p, p]

    wf = InterpolatePoints(values=values, duration=t)

    assert all(
        k == p == v
        for k, p, v in zip(wf.values, np.array(values), values)  # type: ignore [arg-type]
    )
    assert wf.times is None

    with pytest.raises(AssertionError):
        InterpolatePoints(values=values, duration="t")

    times = np.linspace(0, 1, num=len(values))
    wf2 = InterpolatePoints(values=values, duration=t, times=times)

    assert wf2.times is not None


def test_analog_gate(
    constant_interpolate_points: InterpolatePoints,
    linear_interpolate_points: InterpolatePoints,
    null_interpolate_points: InterpolatePoints,
    square_coords: list,
) -> None:
    """testing `HamiltonianGate` class correctness"""

    ampl = constant_interpolate_points
    det = linear_interpolate_points
    phase = 0.0

    hg = HamiltonianGate(ampl, det, phase, coords=square_coords)

    with pytest.raises(ValueError):
        # amplitude and detuning values must have the same duration
        HamiltonianGate(
            InterpolatePoints([0.0, 0.0], duration=1000),
            InterpolatePoints([0.0, 0.0], duration=900),
            phase,
            coords=square_coords,
        )

    with pytest.raises(ValueError):
        HamiltonianGate(
            InterpolatePoints([0.0, 0.0]),
            InterpolatePoints([0.0, 0.0, 0.0]),
            phase,
            coords=square_coords,
        )

    # should work with phase as InterpolatePoints as well
    assert HamiltonianGate(ampl, det, null_interpolate_points, coords=square_coords)

    with pytest.raises(TypeError):
        # amplitude must be InterpolatePoints
        HamiltonianGate([0, 0, 0], det, null_interpolate_points, coords=square_coords)

    with pytest.raises(TypeError):
        # detuning must be InterpolatePoints
        HamiltonianGate(ampl, [0, 0, 0], null_interpolate_points, coords=square_coords)

    with pytest.raises(TypeError):
        # phase must be either InterpolatePoints, float or ParameterExpression
        HamiltonianGate(ampl, det, [0, 0, 0], coords=square_coords)

    _analog_register = PasqalRegister.from_coordinates(square_coords, prefix="q")

    assert np.all([hg.analog_register, _analog_register])  # type: ignore [arg-type]
    assert np.all([hg.coords, _analog_register.qubits])  # type: ignore [arg-type]

    with pytest.raises(AttributeError):
        hg.control()

    with pytest.raises(AttributeError):
        hg.power(2.0)

    with pytest.raises(CircuitError):
        hg.to_matrix()

    qc = QuantumCircuit(len(square_coords))
    assert qc.append(hg, qc.qubits)

    for instruction in qc.data:
        assert isinstance(instruction.operation, HamiltonianGate)
