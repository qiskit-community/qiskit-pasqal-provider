"""Pasqal backends"""

import copy
import logging
import uuid
from abc import ABC
from typing import Union, Optional, Callable

from pulser.devices import (
    Device as PasqalDevice,
    AnalogDevice as PasqalAnalogDevice,
)
from pulser.register import Register as PasqalRegister
from pulser.sequence import Sequence as PasqalSequence
from pulser_simulation import QutipEmulator as PasqalSolver
from qiskit import QuantumCircuit
from qiskit.circuit import Instruction
from qiskit.providers import BackendV2, Options, QubitProperties
from qiskit.pulse import Schedule, ScheduleBlock
from qiskit.pulse.instruction_schedule_map import InstructionScheduleMap
from qiskit.transpiler import Target

from qiskit_pasqal_provider.providers.pasqal_utils import to_pulser

from .pasqal_job import PasqalJob, PasqalLocalJob


logger = logging.getLogger(__name__)


class PasqalBackend(BackendV2, ABC):
    """PasqaqlBackend."""


class PasqalLocalBackend(PasqalBackend):
    """PasqalLocalBackend."""

    def __init__(
        self,
        register: PasqalRegister,
        device: PasqalDevice = PasqalAnalogDevice,
        solver: Callable = PasqalSolver,
        target: Optional[Target] = None,
        **options,
    ):
        """PasqalLocalBackend for executing pulses sequence locally.

        Args:
            register: Pasqal `Register` instance.
            device: Pasqal Device instance. Default is `AnalogDevice`.
            solver: PasqalSolver instance configured for pulse simulation.
                Default is Pulser's `QutipEmulator`.
            target: `Target` object.
            **options: Additional configuration options for the simulator.
        """
        self.backend_name = self.__class__.__name__
        super().__init__(name=self.backend_name, **options)
        self._device = device
        self._register = register
        self._status = None
        self._options.solver = None
        self._options.subsystem_dims = None

        self.set_options(solver=solver, **options)

        if target is None:
            target = Target()
        else:
            target = copy.copy(target)

        # rework on this whole section:
        # add default simulator measure instructions
        # measure_properties = {}
        # instruction_schedule_map = target.instruction_schedule_map()
        # for qubit in range(len(self.options.subsystem_dims)):
        #     if not instruction_schedule_map.has(instruction="measure", qubits=qubit):
        #         with pulse.build() as meas_sched:
        #             pulse.acquire(
        #                 duration=1, qubit_or_channel=qubit, register=pulse.MemorySlot(qubit)
        #             )
        #
        #         measure_properties[(qubit,)] = InstructionProperties(calibration=meas_sched)
        #
        # if bool(measure_properties):
        #     target.add_instruction(Measure(), measure_properties)

        target.dt = None  # Should it be resolved directly by the QutipEmulator somehow?
        # target.num_qubits = len(self.options.subsystem_dims)

        self._target = target  # Implement PasqalTarget for verification?

    @property
    def target(self) -> Target:
        return self._target

    @property
    def max_circuits(self) -> None:
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
        raise NotImplementedError(f"Measurement map is not supported by {self.name}.")

    @property
    def device(self) -> PasqalDevice:
        """
        returns instance's device property (must be pulser device object).
        """
        return self._device

    @property
    def instructions(self) -> list[tuple[Instruction, tuple[int]]]:
        """A list of Instruction tuples on the backend of the form ``(instruction, (qubits)``"""
        return self.target.instructions

    @property
    def operations(self) -> list[Instruction]:
        """A list of :class:`~qiskit.circuit.Instruction` instances that the backend supports."""
        return list(self.target.operations)

    @property
    def operation_names(self) -> list[str]:
        """A list of instruction names that the backend supports."""
        return list(self.target.operation_names)

    def qubit_properties(
        self, qubit: Union[int, list[int]]
    ) -> Union[QubitProperties, list[QubitProperties]]:
        raise NotImplementedError

    @property
    def dt(self) -> Union[float, None]:
        """Return the system time resolution of input signals

        This is required to be implemented if the backend supports Pulse
        scheduling.

        Returns:
            The input signal timestep in seconds.
            If the backend doesn't define ``dt``, ``None`` will be returned.
        """
        return self.target.dt if hasattr(self.target, "dt") else None

    @property
    def instruction_schedule_map(self) -> InstructionScheduleMap:
        """Return the :class:`~qiskit.pulse.InstructionScheduleMap` for the
        instructions defined in this backend's target."""
        return self.target.instruction_schedule_map()

    def run(
        self, run_input: Union[QuantumCircuit, Schedule, ScheduleBlock], **options
    ) -> PasqalJob:
        """Run a program on Pasqal backend"""
        if isinstance(run_input, QuantumCircuit):
            raise NotImplementedError(
                "Conversion of QuantumCircuit to Pulses not implemented"
            )
        if isinstance(run_input, ScheduleBlock):
            raise NotImplementedError("ScheduleBlocks not yet supported")

        seq = PasqalSequence(self._register, PasqalAnalogDevice)
        seq.declare_channel("rydberg_global", "rydberg_global")

        pulser_pulses = to_pulser(run_input)
        for pulse, channel in pulser_pulses:
            seq.add(pulse, channel)

        # initialise the backend from sequence.
        # In the sequence the register and device is encoded
        # we can imagine moving that to the Qiskit Backend
        emulator = self._options.solver.from_sequence(seq)
        backend = copy.deepcopy(self)
        job_id = str(uuid.uuid4())
        return PasqalLocalJob(backend, job_id, emulator)
