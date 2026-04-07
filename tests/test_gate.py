"""Testing `HamiltonianGate` and `InterpolatePoints` classes."""

import pytest

import numpy as np
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.circuit.exceptions import CircuitError
from qiskit.primitives import PrimitiveResult

from qiskit_pasqal_provider.providers.pulse_utils import (
    PasqalRegister,
    InterpolatePoints,
    ObjWrapper,
)
from qiskit_pasqal_provider.providers.gate import (
    HamiltonianGate,
    dumps_qpp_openqasm3,
    loads_qpp_openqasm3,
)
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.sampler import SamplerV2


def test_interpolate_points() -> None:
    """testing `InterpolatePoints` class correctness."""

    p = Parameter("p")
    t = Parameter("t")
    values = [0, 1 / 3 * p, 2 / 3 * p, p]

    wf = InterpolatePoints(values=values, duration=t)

    assert all(k == p == v for k, p, v in zip(wf.values, np.array(values), values))
    assert wf.times is None

    with pytest.raises(AssertionError):
        InterpolatePoints(values=values, duration="t")

    times = np.linspace(0, 1, num=len(values))
    wf2 = InterpolatePoints(values=values, duration=t, times=times)

    assert wf2.times is not None


def test_obj_wrapper_handles_none_inputs() -> None:
    """testing `ObjWrapper` with None inputs."""

    wrapper = ObjWrapper(None, None)
    assert wrapper.data == ()
    assert wrapper.size == 0


@pytest.mark.parametrize("phase", [0.0, InterpolatePoints([0, 0])])
def test_analog_gate(
    phase: float | InterpolatePoints,
    constant_interpolate_points: InterpolatePoints,
    linear_interpolate_points: InterpolatePoints,
    square_coords: list,
) -> None:
    """testing `HamiltonianGate` class correctness"""

    ampl = constant_interpolate_points
    det = linear_interpolate_points

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
    assert HamiltonianGate(ampl, det, InterpolatePoints([0, 0]), coords=square_coords)

    with pytest.raises(TypeError):
        # amplitude must be InterpolatePoints
        HamiltonianGate(
            [0, 0, 0],  # type: ignore [arg-type]
            det,
            InterpolatePoints([0, 0]),  # type ignore [arg-type]
            coords=square_coords,
        )

    with pytest.raises(TypeError):
        # detuning must be InterpolatePoints
        HamiltonianGate(
            ampl,
            [0, 0, 0],  # type: ignore [arg-type]
            InterpolatePoints([0, 0]),
            coords=square_coords,
        )

    with pytest.raises(TypeError):
        # phase must be either InterpolatePoints, float or ParameterExpression
        HamiltonianGate(ampl, det, [0, 0, 0], coords=square_coords)

    p = Parameter("p")
    phase_expr_gate = HamiltonianGate(ampl, det, p + 0.1, coords=square_coords)
    assert p in phase_expr_gate.params

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


def test_openqasm3_transport_roundtrip_scalar_phase(square_coords: list) -> None:
    """testing OpenQASM3 transport roundtrip with scalar phase."""

    pytest.importorskip("qiskit_qasm3_import")

    ampl = InterpolatePoints(values=[0.0, 4.0, 4.0, 0.0], times=[0.0, 0.2, 0.8, 1.0])
    det = InterpolatePoints(
        values=[-10.0, -10.0, -5.0, -5.0], times=[0.0, 0.2, 0.8, 1.0]
    )
    phase = 0.3
    gate = HamiltonianGate(
        ampl, det, phase, coords=square_coords, grid_transform="square", transform=True
    )

    qc = QuantumCircuit(len(square_coords))
    qc.append(gate, qc.qubits)

    qasm = dumps_qpp_openqasm3(qc)
    restored = loads_qpp_openqasm3(qasm)
    restored_gate = restored.data[0].operation
    assert isinstance(restored_gate, HamiltonianGate)
    assert np.allclose(restored_gate.amplitude.values, ampl.values)
    assert np.allclose(restored_gate.detuning.values, det.values)
    assert np.allclose(restored_gate.amplitude.times, ampl.times)
    assert np.allclose(restored_gate.detuning.times, det.times)
    assert restored_gate.phase == phase

    result = SamplerV2(PasqalProvider().get_backend("qutip")).run([restored]).result()
    assert isinstance(result, PrimitiveResult)


def test_openqasm3_transport_roundtrip_phase_waveform(square_coords: list) -> None:
    """testing OpenQASM3 transport roundtrip with phase waveform."""

    pytest.importorskip("qiskit_qasm3_import")

    times = [0.0, 0.2, 0.8, 1.0]
    ampl = InterpolatePoints(values=[0.0, 4.0, 4.0, 0.0], times=times)
    det = InterpolatePoints(values=[-10.0, -10.0, -5.0, -5.0], times=times)
    phase = InterpolatePoints(values=[0.0, 0.0, 0.3, 0.3], times=times)
    gate = HamiltonianGate(
        ampl, det, phase, coords=square_coords, grid_transform="square", transform=True
    )

    qc = QuantumCircuit(len(square_coords))
    qc.append(gate, qc.qubits)
    restored = loads_qpp_openqasm3(
        dumps_qpp_openqasm3(qc)
    )
    restored_gate = restored.data[0].operation
    assert isinstance(restored_gate, HamiltonianGate)
    assert isinstance(restored_gate.phase, InterpolatePoints)
    assert np.allclose(restored_gate.phase.values, phase.values)
    assert np.allclose(restored_gate.phase.times, phase.times)


def test_openqasm3_transport_rejects_parametric_phase(square_coords: list) -> None:
    """testing OpenQASM3 transport rejects unresolved parameter expressions."""

    p = Parameter("p")
    gate = HamiltonianGate(
        InterpolatePoints(values=[0.0, 4.0, 4.0, 0.0], times=[0.0, 0.2, 0.8, 1.0]),
        InterpolatePoints(values=[-10.0, -10.0, -5.0, -5.0], times=[0.0, 0.2, 0.8, 1.0]),
        p,
        coords=square_coords,
    )
    qc = QuantumCircuit(len(square_coords))
    qc.append(gate, qc.qubits)

    with pytest.raises(ValueError, match="phase must be numeric"):
        dumps_qpp_openqasm3(qc)
