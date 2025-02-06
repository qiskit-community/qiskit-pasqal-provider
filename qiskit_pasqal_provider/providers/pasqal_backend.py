"""Pasqal backends"""

import copy
import logging
import uuid
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Union

from pulser.sequence import Sequence as PasqalSequence
from pulser.register import Register
from pulser_simulation import QutipEmulator
from qiskit import QuantumCircuit
from qiskit.providers import BackendV2, Options
from qiskit.pulse import Schedule, ScheduleBlock

from .pasqal_job import PasqalJob, PasqalLocalJob
from .pasqal_utils import PasqalRegister, to_pulser
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


class QutipEmulatorBackend(BackendV2):
    """QutipEmulatorBackend to emulate pulse sequences using QuTiP."""

    def __init__(self, target: PasqalTarget, **options: Any):
        """

        Args:
            target (PasqalTarget): The target of the pulse sequence.
            **options: additional configuration options
        """

        self.backend_name = self.__class__.__name__
        super().__init__(name=self.backend_name, **options)
        self.backend = "qutip"
        self._target = target
        self._layout = self.target.layout

    @property
    def target(self) -> PasqalTarget:
        return self._target

    @property
    def max_circuits(self) -> None:
        # check whether it is essential for class to work
        return None  # No max

    @classmethod
    def _default_options(cls) -> Options:
        return Options()

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

        if register is None:
            raise ValueError("register cannot be None")

        # Run a program on Pasqal backend
        if isinstance(run_input, QuantumCircuit):
            raise NotImplementedError(
                "Conversion of QuantumCircuit to Pulses not implemented"
            )
        if isinstance(run_input, ScheduleBlock):
            raise NotImplementedError("ScheduleBlocks not yet supported")

        seq = PasqalSequence(register, self.target.device)
        seq.declare_channel("rydberg_global", "rydberg_global")

        pulser_pulses = to_pulser(run_input)
        for pulse, channel in pulser_pulses:
            seq.add(pulse, channel)

        # initialise the backend from sequence.
        # In the sequence the register and device is encoded
        # we can imagine moving that to the Qiskit Backend
        emulator = QutipEmulator.from_sequence(seq)
        backend = copy.deepcopy(self)
        job_id = str(uuid.uuid4())
        return PasqalLocalJob(backend, job_id, emulator)


class EmuMpsBackend(BackendV2):
    """PasqalEmuMpsBackend."""

    def __init__(self, target: PasqalTarget, **options: Any):
        """
        defines the EMU-MPS backend instance.

        Args:
            target (PasqalTarget): the Pasqal target instance
            **options: additional configuration options for the backend
        """
        # super().__init__(target=target, backend="emu-mps")
        self.backend_name = self.__class__.__name__
        super().__init__(name=self.backend_name, **options)
        self.backend = "qutip"
        self._target = target
        self._layout = self.target.layout

    @property
    def target(self) -> PasqalTarget:
        return self._target

    @property
    def max_circuits(self) -> None:
        # check whether it is essential for class to work
        return None  # No max

    @classmethod
    def _default_options(cls) -> Options:
        return Options()

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
