"""Test sampler instance"""

import pytest
from qiskit import QuantumCircuit

from qiskit_pasqal_provider.providers.sampler import Sampler
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.gate import HamiltonianGate, InterpolatePoints
from qiskit_pasqal_provider.providers.result import PasqalResult


@pytest.mark.parametrize("backend_name", ["qutip", "emu-mps"])
def test_local_sampler_backends(backend_name: str, square_coords: list) -> None:
    """Testing sampler instance with qutip emulator (local provider)."""

    # analog gate properties
    ampl = InterpolatePoints(values=[1, 1, 1])
    det = InterpolatePoints(values=[0, 0.5, 1])
    phase = 0.0

    # analog gate
    gate = HamiltonianGate(ampl, det, phase, square_coords, grid_transform="square")

    # qiskit circuit with analog gate
    qc = QuantumCircuit(4)
    qc.append(gate, qc.qubits)

    provider = PasqalProvider()
    backend = provider.get_backend(backend_name)
    sampler = Sampler(backend)
    results = sampler.run([qc]).result()

    assert isinstance(results, PasqalResult)
