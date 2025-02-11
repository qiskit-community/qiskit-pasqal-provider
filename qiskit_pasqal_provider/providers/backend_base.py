"""Pasqal backends"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Union

from .backends.emu_mps import EmuMpsBackend
from .backends.qutip import QutipEmulatorBackend

try:
    from enum import StrEnum
except ImportError:
    from qiskit_pasqal_provider.utils import StrEnum  # type: ignore [assignment]

from pulser.register import Register
from qiskit import QuantumCircuit
from qiskit.providers import BackendV2
from qiskit.pulse import Schedule, ScheduleBlock

from .jobs import PasqalJob
from .pulse_utils import PasqalRegister
from .pasqal_devices import PasqalTarget

logger = logging.getLogger(__name__)


class PasqalBackendType(StrEnum):
    """Pasqal backend StrEnum to choose between emulators/QPUs"""

    QUTIP = "qutip"
    EMUMPS = "emu-mps"
    QPU = "qpu"


class PasqalBackend(BackendV2, ABC):
    """PasqaqlBackend base class."""

    @abstractmethod
    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
        **options: Any,
    ) -> PasqalJob:
        pass


class PasqalLocalBackend(PasqalBackend):
    """PasqalLocalBackend."""

    def __new__(
        cls,
        target: PasqalTarget,
        backend: PasqalBackendType | str | None = None,
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


class PasqalRemoteBackend(PasqalBackend):
    """PasqalRemoteBackend."""

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
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | Register | None = None,
        **options: Any,
    ) -> PasqalJob:
        """

        Args:
            run_input (QuantumCircuit, Schedule, ScheduleBlock): the block of instructions
                to be run
            register (PasqalRegister): the register to be used in the instruction execution
            **options: additional configuration options for the run

        Returns:
            A PasqalJob instance.
        """
        raise NotImplementedError()
