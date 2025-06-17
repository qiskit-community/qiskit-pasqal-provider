"""Test sampler instance"""

from sys import platform

import pytest
from pulser import Sequence, Register
from qiskit.circuit import QuantumCircuit, Parameter


from qiskit_pasqal_provider.providers.sampler import Sampler
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.gate import HamiltonianGate
from qiskit_pasqal_provider.providers.pulse_utils import InterpolatePoints
from qiskit_pasqal_provider.providers.result import PasqalResult
from qiskit_pasqal_provider.providers.target import AVAILABLE_DEVICES


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
            marks=pytest.mark.skipif(platform in ["win32", "cygwin"], reason="Windows"),
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
    sampler = Sampler(backend)
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
    ]
)
@pytest.mark.parametrize(
    "backend_name",
    [
        "qutip",
        pytest.param(
            "emu-mps",
            marks=pytest.mark.skipif(platform in ["win32", "cygwin"], reason="Windows"),
        ),
    ],
)
def test_local_sampler_backends_parametric(
    backend_name: str, phase: float | InterpolatePoints, extra: tuple, square_coords: list
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
    sampler = Sampler(backend)

    if isinstance(phase, InterpolatePoints):
        if isinstance(phase.values[0], Parameter):
            p = phase.values[0]
            results = sampler.run([(qc, {a: [1, 1, 1], d: [0, 0.5, 1], p: extra})]).result()

        else:
            results = sampler.run([(qc, {a: [1, 1, 1], d: [0, 0.5, 1]})]).result()

    else:
        results = sampler.run([(qc, {a: [1, 1, 1], d: [0, 0.5, 1]})]).result()

    assert isinstance(results, PasqalResult)
