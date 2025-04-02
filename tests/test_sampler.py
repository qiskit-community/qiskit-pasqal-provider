"""Test sampler instance"""

import pytest

from qiskit import QuantumCircuit

from qiskit_pasqal_provider.providers.sampler import Sampler
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.backends.qutip import QutipEmulatorBackend
from qiskit_pasqal_provider.providers.jobs import PasqalResult


def test_local_sampler_qutip() -> None:
    """Testing sampler instance with qutip emulator (local provider)."""

    qc = QuantumCircuit(2)

    provider = PasqalProvider()
    backend = provider.get_backend("qutip")
    sampler = Sampler(backend)
    results = sampler.run([]).result()
    print(results)

    assert isinstance(results, PasqalResult)
