"""Test sampler instance"""

from sys import platform

import pytest
from pulser import Sequence, Register
from qiskit.circuit import QuantumCircuit, Parameter


from qiskit_pasqal_provider.providers.sampler import Sampler
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.gate import HamiltonianGate, InterpolatePoints
from qiskit_pasqal_provider.providers.result import PasqalResult
from qiskit_pasqal_provider.providers.target import AVAILABLE_DEVICES


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
def test_local_sampler_backends(backend_name: str, square_coords: list) -> None:
    """Testing sampler instance with qutip and emu-mps emulators (local provider)."""

    # analog gate properties
    ampl = InterpolatePoints(values=[1, 1, 1])
    det = InterpolatePoints(values=[0, 0.5, 1])
    phase = 0.0

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
    backend_name: str, square_coords: list
) -> None:
    """
    Testing sampler instance with qutip and emu-mps emulators (local provider) with
    parametric values.
    """

    p = Parameter("p")
    d = Parameter("d")

    # analog gate properties
    ampl = InterpolatePoints(values=p, n=4)
    det = InterpolatePoints(values=d, n=4)
    phase = 0.0

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
    results = sampler.run([(qc, {p: [1, 1, 1, 1], d: [0, 1 / 3, 2 / 3, 1]})]).result()

    assert isinstance(results, PasqalResult)
