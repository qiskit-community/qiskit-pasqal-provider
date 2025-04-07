"""Test sampler instance"""

from qiskit import QuantumCircuit

from qiskit_pasqal_provider.providers.sampler import Sampler
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.gate import HamiltonianGate, InterpolatePoints
from qiskit_pasqal_provider.providers.result import PasqalResult


def test_local_sampler_qutip(square_coords: list) -> None:
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
    backend = provider.get_backend("qutip")
    sampler = Sampler(backend)
    results = sampler.run([qc]).result()

    assert isinstance(results, PasqalResult)
