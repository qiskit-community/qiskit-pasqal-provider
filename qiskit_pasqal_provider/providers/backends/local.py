"""Local base backend"""

from typing import Any

from qiskit import QuantumCircuit

from qiskit_pasqal_provider.providers.backend_base import (
    PasqalBackend,
    PasqalBackendType,
)
from qiskit_pasqal_provider.providers.backends.emu_mps import EmuMpsBackend
from qiskit_pasqal_provider.providers.backends.qutip import QutipEmulatorBackend
from qiskit_pasqal_provider.providers.job_base import PasqalJob
from qiskit_pasqal_provider.providers.target import PasqalTarget


class PasqalLocalBackend(PasqalBackend):
    """PasqalLocalBackend."""

    def __new__(
        cls,
        backend: PasqalBackendType | str,
        target: PasqalTarget | None = None,
        **options: Any,
    ) -> Any:
        """creates a proper backend instance."""

        if target is None:
            target = PasqalTarget()

        match backend:
            case "qutip":
                return QutipEmulatorBackend(target=target, **options)

            case "emu-mps":
                return EmuMpsBackend(target=target, **options)

            case _:
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
            run_input: the quantum circuit to be run.
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            **options: extra options to pass to the backend if needed.

        Returns:
            A PasqalJob instance containing the results from the execution interface.
        """
        raise NotImplementedError()

    @property
    def target(self) -> Any:
        raise NotImplementedError()

    @property
    def max_circuits(self):
        raise NotImplementedError()

    @classmethod
    def _default_options(cls) -> Any:
        raise NotImplementedError()
