"""Pasqal backends"""

import copy
import logging
import uuid
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Union

from pulser.sequence import Sequence as PasqalSequence
from pulser_simulation import QutipEmulator
from qiskit import QuantumCircuit
from qiskit.circuit import Instruction
from qiskit.providers import BackendV2, Options, QubitProperties
from qiskit.pulse import Schedule, ScheduleBlock
from qiskit.pulse.instruction_schedule_map import InstructionScheduleMap

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
        cls, target: PasqalTarget, backend: PasqalBackendType | str, **options: Any
    ) -> Any:
        match backend:
            case "qutip":
                return QutipEmulatorBackend(target, **options)

            case "emu-mps":
                return EmuMpsBackend(target, **options)

            case _:
                raise NotImplementedError()

    def __init__(
        self,
        target: PasqalTarget,
        backend: str,
        **options: Any,
    ):
        """PasqalLocalBackend for executing pulses sequence locally.

        Args:
            register: Pasqal `Register` instance.
            target: Pasqal Device instance. Default is `AnalogDevice`.
            solver: PasqalSolver instance configured for pulse simulation.
                Default is Pulser's `QutipEmulator`.
            target: `Target` object.
            **options: Additional configuration options for the simulator.
        """

        self.backend_name = self.__class__.__name__
        super().__init__(name=self.backend_name, **options)

        self.backend = backend
        self._device = target
        self._layout = self.device.layout
        self._status = None

        # check whether it is essential for class to work
        self._target = target

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

    @property  # Find out which of these boilerplates are truly needed to implement
    def dtm(self) -> float:
        raise NotImplementedError(
            f"System time resolution of output signals is not supported by {self.name}."
        )

    @property
    def meas_map(self) -> list[list[int]]:
        # check whether it is essential for class to work
        raise NotImplementedError(f"Measurement map is not supported by {self.name}.")

    @property
    def device(self) -> PasqalTarget:
        """
        returns instance's device property (must be pulser device object).
        """
        return self._device

    @property
    def instructions(self) -> list[tuple[Instruction, tuple[int]]]:
        # check whether it is essential for class to work
        """A list of Instruction tuples on the backend of the form ``(instruction, (qubits)``"""
        raise NotImplementedError()

    @property
    def operations(self) -> list[Instruction]:
        # check whether it is essential for class to work
        """A list of :class:`~qiskit.circuit.Instruction` instances that the backend supports."""
        raise NotImplementedError()

    @property
    def operation_names(self) -> list[str]:
        # check whether it is essential for class to work
        """A list of instruction names that the backend supports."""
        raise NotImplementedError()

    def qubit_properties(
        self, qubit: Union[int, list[int]]
    ) -> Union[QubitProperties, list[QubitProperties]]:
        # check whether it is essential for class to work
        raise NotImplementedError()

    @property
    def dt(self) -> Union[float, None]:
        # check whether it is essential for class to work
        """Return the system time resolution of input signals

        This is required to be implemented if the backend supports Pulse
        scheduling.

        Returns:
            The input signal timestep in seconds.
            If the backend doesn't define ``dt``, ``None`` will be returned.
        """
        raise NotImplementedError()

    @property
    def instruction_schedule_map(self) -> InstructionScheduleMap:
        # check whether it is essential for class to work
        """Return the :class:`~qiskit.pulse.InstructionScheduleMap` for the
        instructions defined in this backend's target."""
        raise NotImplementedError()

    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
        **options: Any,
    ) -> PasqalJob:
        raise NotImplementedError()


class QutipEmulatorBackend(PasqalLocalBackend):
    """QutipEmulatorBackend to emulate pulse sequences using QuTiP."""

    def __init__(self, target: PasqalTarget, **options: Any):
        """

        Args:
            target:
            **options:
        """
        super().__init__(target, "qutip", **options)

    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
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

        seq = PasqalSequence(register, self.device.device)
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


class EmuMpsBackend(PasqalLocalBackend):
    """PasqalEmuMpsBackend."""

    def __init__(self, target: PasqalTarget, **options: Any):
        """
        defines the EMU-MPS backend instance.

        Args:
            target (PasqalTarget): the Pasqal target instance
            **options:
        """
        super().__init__(target, "emu-mps", **options)

    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
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

    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
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
