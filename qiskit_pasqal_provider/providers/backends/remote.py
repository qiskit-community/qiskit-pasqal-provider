"""Remote base backend"""

from typing import Any

from qiskit import QuantumCircuit

from qiskit_pasqal_provider.providers.backend_base import (
    PasqalBackend,
    PasqalBackendType,
)
from qiskit_pasqal_provider.providers.backends.emu_tn import EmuTnBackend
from qiskit_pasqal_provider.providers.backends.emu_free import EmuFreeBackend
from qiskit_pasqal_provider.providers.backends.qpu import QPUBackend
from qiskit_pasqal_provider.providers.job_base import PasqalJob
from qiskit_pasqal_provider.utils import RemoteConfig


class PasqalRemoteBackend(PasqalBackend):
    """PasqalRemoteBackend."""

    def __new__(
        cls,
        backend: PasqalBackendType | str,
        remote_config: RemoteConfig,
        **_options: Any,
    ):
        # cloud = PasqalCloud
        match backend:
            case "remote-emu-free":
                return EmuFreeBackend(remote_config)

            case "remote-emu-tn":
                return EmuTnBackend(remote_config)

            case "qpu":
                return QPUBackend(remote_config)

            case _:
                raise NotImplementedError()

    @property
    def target(self):
        raise NotImplementedError()

    @property
    def max_circuits(self):
        raise NotImplementedError()

    @classmethod
    def _default_options(cls):
        raise NotImplementedError()

    def run(
        self,
        run_input: QuantumCircuit,
        shots: int | None = None,
        values: dict | None = None,
        **options: Any,
    ) -> PasqalJob:
        """
        Run a quantum circuit for a given execution interface, namely `Sampler`.

        Args:
            run_input (QuantumCircuit): the quantum circuit to be run
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            **options: additional configuration options for the run

        Returns:
            A PasqalJob instance.
        """
        raise NotImplementedError()
