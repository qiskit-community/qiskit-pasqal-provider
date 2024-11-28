"""Pasqal backends"""

import copy
import logging
import uuid
from abc import ABC
from typing import Union

import pulser
from pulser.devices import Device
from pulser_simulation import QutipEmulator
from qiskit import QuantumCircuit
from qiskit.circuit import Instruction
from qiskit.providers import BackendV2, Options, QubitProperties
from qiskit.pulse import Schedule, ScheduleBlock
from qiskit.pulse.instruction_schedule_map import InstructionScheduleMap
from qiskit.transpiler import Target

from .pasqal_job import PasqalJob, PasqalLocalJob

logger = logging.getLogger(__name__)


class PasqalBackend(BackendV2, ABC):
    """PasqaqlBackend."""

    def __repr__(self) -> str:
        return f"PasqalBackend[{self.name}]"


class PasqalLocalBackend(PasqalBackend):
    """BraketLocalBackend."""

    def __init__(self, name: str = "default", **fields):
        """PasqalLocalBackend for executing circuits locally.

        Example:
            >>> device = PasqalLocalBackend()                    #Local State Vector Simulator
            >>> device = PasqalLocalBackend("default")           #Local State Vector Simulator
            >>> device = PasqalLocalBackend(name="default")      #Local State Vector Simulator
            >>> device = PasqalLocalBackend(name="qutip_sv")     #Local State Vector Simulator
            >>> device = PasqalLocalBackend(name="qutip_dm")     #Local Density Matrix Simulator

        Args:
            name: name of backend
            **fields: extra fields
        """
        super().__init__(name=name, **fields)
        self.backend_name = name
        self._status = None
        self._target = None  # TODO: implement PasqalTarget for verification

    @property
    def target(self) -> Target:
        return self.target

    @property
    def max_circuits(self) -> None:
        return None  # No max

    @classmethod
    def _default_options(cls) -> Options:
        return Options()

    @property  # TODO: find out which of these boilerplates are truly needed to implement
    def dtm(self) -> float:
        raise NotImplementedError(
            f"System time resolution of output signals is not supported by {self.name}."
        )

    @property
    def meas_map(self) -> list[list[int]]:
        raise NotImplementedError(f"Measurement map is not supported by {self.name}.")

    @property
    def _device(self) -> Device:
        return None  # Fixme

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
            The input signal timestep in seconds. If the backend doesn't define ``dt``, ``None`` will
            be returned.
        """
        return self.target.dt

    @property
    def dtm(self) -> float:
        """Return the system time resolution of output signals

        Returns:
            The output signal timestep in seconds.

        Raises:
            NotImplementedError: if the backend doesn't support querying the
                output signal timestep
        """
        raise NotImplementedError

    @property
    def meas_map(self) -> list[list[int]]:
        """Return the grouping of measurements which are multiplexed

        This is required to be implemented if the backend supports Pulse
        scheduling.

        Returns:
            The grouping of measurements which are multiplexed
        """
        raise NotImplementedError

    @property
    def instruction_schedule_map(self) -> InstructionScheduleMap:
        """Return the :class:`~qiskit.pulse.InstructionScheduleMap` for the
        instructions defined in this backend's target."""
        return self.target.instruction_schedule_map()

    def run(  # type: ignore
        self, run_input: Union[QuantumCircuit, Schedule, ScheduleBlock], **options
    ) -> PasqalJob:
        if isinstance(run_input, QuantumCircuit):
            raise NotImplementedError(
                "Conversion of QuantumCircuit to Pulses not implemented"
            )
        elif isinstance(run_input, ScheduleBlock):
            raise NotImplemented("ScheduleBlocks not yet supported")
        pulser_sequence = to_pulser(run_input)
        emulator = QutipEmulator.from_sequence(pulser_sequence)
        backend = copy.deepcopy(self)
        job_id = str(uuid.uuid4())
        return PasqalLocalJob(backend, job_id, emulator)


def to_pulser(sched: Schedule) -> pulser.Sequence:
    # TODO, convert from Schedule...
    reg = pulser.Register.rectangle(1, 2, spacing=8, prefix="atom")
    pulse = pulser.Pulse.ConstantPulse(200, 2, -10, 0)

    seq = pulser.Sequence(reg, pulser.AnalogDevice)
    seq.declare_channel("rydberg_global", "rydberg_global")
    seq.add(pulse, "rydberg_global")

    return seq
