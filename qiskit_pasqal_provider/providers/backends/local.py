"""Local base backend"""

from typing import Any, Union

from pulser import Register
from qiskit import QuantumCircuit
from qiskit.pulse import Schedule, ScheduleBlock

from qiskit_pasqal_provider.providers.backend_base import (
    PasqalBackend,
    PasqalBackendType,
)
from qiskit_pasqal_provider.providers.backends.emu_mps import EmuMpsBackend
from qiskit_pasqal_provider.providers.backends.qutip import QutipEmulatorBackend
from qiskit_pasqal_provider.providers.jobs import PasqalJob
from qiskit_pasqal_provider.providers.pasqal_devices import PasqalTarget
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister


class PasqalLocalBackend(PasqalBackend):
    """PasqalLocalBackend."""

    def __new__(
        cls,
        target: PasqalTarget,
        backend: PasqalBackendType | str,
        **options: Any,
    ) -> Any:
        """creates a proper backend instance."""

        match backend:
            case "qutip":
                return QutipEmulatorBackend(target=target, **options)

            case "emu-mps":
                return EmuMpsBackend(target=target, **options)

            case _:
                raise NotImplementedError()

    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | Register | None = None,
        **options: Any,
    ) -> PasqalJob:
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
