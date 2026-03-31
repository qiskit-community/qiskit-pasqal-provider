"""Test sampler instance"""

from importlib.util import find_spec
from sys import platform

import pytest
from pulser import Register, Sequence
from qiskit.circuit import Parameter, QuantumCircuit

from qiskit_pasqal_provider.providers.gate import HamiltonianGate, InterpolatePoints
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.result import PasqalResult
from qiskit_pasqal_provider.providers.sampler import SamplerV2
from qiskit_pasqal_provider.providers.target import AVAILABLE_DEVICES

HAS_EMU_MPS = find_spec("emu_mps") is not None


@pytest.mark.parametrize(
    "phase",
    [
        0.0,
        InterpolatePoints(
            values=[
                0.0,
                0.0,
            ]
        ),
        InterpolatePoints(values=[0, 1.0]),
        InterpolatePoints(values=[0.0, 0.0, 0.0]),
    ],
)
@pytest.mark.parametrize(
    "backend_name",
    [
        "qutip",
        pytest.param(
            "emu-mps",
            marks=pytest.mark.skipif(
                platform in ["win32", "cygwin"] or not HAS_EMU_MPS,
                reason="Windows or missing emu_mps dependency",
            ),
        ),
    ],
)
def test_local_sampler_backends(
    backend_name: str, phase: float | InterpolatePoints, square_coords: list
) -> None:
    """Testing sampler instance with qutip and emu-mps emulators (local provider)."""

    # analog gate properties
    ampl = InterpolatePoints(values=[1, 1, 1])
    det = InterpolatePoints(values=[0, 0.5, 1])

    # analog gate
    gate = HamiltonianGate(
        ampl, det, phase, square_coords, grid_transform="square", transform=True
    )

    # qiskit circuit with analog gate
    qc = QuantumCircuit(4)
    qc.append(gate, qc.qubits)

    provider = PasqalProvider()
    backend = provider.get_backend(backend_name)
    sampler = SamplerV2(backend)
    results = sampler.run([qc]).result()

    assert isinstance(results, PasqalResult)

    with pytest.raises(ValueError):
        seq = Sequence(Register({"q0": (2, -1)}), device=AVAILABLE_DEVICES["analog"])
        sampler.run([seq])


@pytest.mark.parametrize(
    "phase,extra",
    [
        (0.0, ()),
        (InterpolatePoints(values=Parameter("p"), n=3), (0, 1, 0)),
        (InterpolatePoints(values=[0, 1.0, 0]), ()),
    ],
)
@pytest.mark.parametrize(
    "backend_name",
    [
        "qutip",
        pytest.param(
            "emu-mps",
            marks=pytest.mark.skipif(
                platform in ["win32", "cygwin"] or not HAS_EMU_MPS,
                reason="Windows or missing emu_mps dependency",
            ),
        ),
    ],
)
def test_local_sampler_backends_parametric(
    backend_name: str,
    phase: float | InterpolatePoints,
    extra: tuple,
    square_coords: list,
) -> None:
    """
    Testing sampler instance with qutip and emu-mps emulators (local provider) with
    parametric values.
    """

    a = Parameter("a")
    d = Parameter("d")

    # analog gate properties
    ampl = InterpolatePoints(values=a, n=3)
    det = InterpolatePoints(values=d, n=3)

    # analog gate
    gate = HamiltonianGate(
        ampl, det, phase, square_coords, grid_transform="square", transform=True
    )

    # qiskit circuit with analog gate
    qc = QuantumCircuit(4)
    qc.append(gate, qc.qubits)

    provider = PasqalProvider()
    backend = provider.get_backend(backend_name)
    sampler = SamplerV2(backend)

    if isinstance(phase, InterpolatePoints):
        if isinstance(phase.values[0], Parameter):
            p = phase.values[0]
            results = sampler.run(
                [(qc, {a: [1, 1, 1], d: [0, 0.5, 1], p: extra})]
            ).result()

        else:
            results = sampler.run([(qc, {a: [1, 1, 1], d: [0, 0.5, 1]})]).result()

    else:
        results = sampler.run([(qc, {a: [1, 1, 1], d: [0, 0.5, 1]})]).result()

    assert isinstance(results, PasqalResult)


def test_sampler_rejects_multiple_pubs(square_coords: list) -> None:
    """Test sampler rejects multiple pubs."""

    gate = HamiltonianGate(
        InterpolatePoints(values=[1, 1, 1]),
        InterpolatePoints(values=[0, 0.5, 1]),
        0.0,
        square_coords,
        grid_transform="square",
        transform=True,
    )

    qc1 = QuantumCircuit(4)
    qc1.append(gate, qc1.qubits)
    qc2 = QuantumCircuit(4)
    qc2.append(gate, qc2.qubits)

    sampler = SamplerV2(PasqalProvider().get_backend("qutip"))
    with pytest.raises(ValueError, match="exactly one pub per run"):
        sampler.run([qc1, qc2], shots=10)


def test_sampler_rejects_empty_circuit() -> None:
    """Test sampler rejects circuits without analog gates."""

    sampler = SamplerV2(PasqalProvider().get_backend("qutip"))
    with pytest.raises(ValueError, match="at least one analog gate"):
        sampler.run([QuantumCircuit(1)], shots=10)


def test_qutip_metadata_uses_qobj_id(square_coords: list) -> None:
    """Test qutip run metadata uses `qobj_id` key."""

    gate = HamiltonianGate(
        InterpolatePoints(values=[1, 1, 1]),
        InterpolatePoints(values=[0, 0.5, 1]),
        0.0,
        square_coords,
        grid_transform="square",
        transform=True,
    )

    qc = QuantumCircuit(4)
    qc.append(gate, qc.qubits)

    result = (
        SamplerV2(PasqalProvider().get_backend("qutip")).run([qc], shots=10).result()
    )
    assert "qobj_id" in result.metadata
    assert "qojb_id" not in result.metadata


@pytest.mark.parametrize(
    "backend_name",
    [
        "qutip",
        pytest.param(
            "emu-mps",
            marks=pytest.mark.skipif(
                platform in ["win32", "cygwin"] or not HAS_EMU_MPS,
                reason="Windows or missing emu_mps dependency",
            ),
        ),
    ],
)
def test_local_sampler_backends_parametric_phase_parameter(
    backend_name: str, square_coords: list
) -> None:
    """Testing sampler instance with qiskit.Parameter as scalar phase."""

    a = Parameter("a")
    d = Parameter("d")
    p = Parameter("p")

    gate = HamiltonianGate(
        InterpolatePoints(values=a, n=3),
        InterpolatePoints(values=d, n=3),
        p,
        square_coords,
        grid_transform="square",
        transform=True,
    )

    qc = QuantumCircuit(4)
    qc.append(gate, qc.qubits)

    provider = PasqalProvider()
    sampler = SamplerV2(provider.get_backend(backend_name))
    results = sampler.run([(qc, {a: [1, 1, 1], d: [0, 0.5, 1], p: 0.1})]).result()

    assert isinstance(results, PasqalResult)
