"""test backends functionalities"""

import pytest

from qiskit import QuantumCircuit, QuantumRegister

from qiskit_pasqal_provider.providers.jobs import PasqalLocalJob
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.backends.qutip import QutipEmulatorBackend
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister


@pytest.skip("it needs 'HamiltonianGate' implemented")
def test_backend_workflow(
    square_register2x2: PasqalRegister,
) -> None:
    """test qutip backend correctness"""

    backend_name = "qutip"
    provider = PasqalProvider()
    backend = provider.get_backend(backend_name)

    assert isinstance(backend, QutipEmulatorBackend)
    assert backend.name == backend_name

    analog_register = square_register2x2
    qc = QuantumCircuit(QuantumRegister(len(analog_register.qubits)))
    # add the HamiltonianGate here

    job = backend.run(qc)

    assert isinstance(job.result(), PasqalLocalJob)
