"""Pasqal custom Schedule for analog neutral atom devices"""

import logging
from copy import copy
from typing import Any

from pulser import Register
from qiskit.circuit import Instruction
from qiskit.pulse import Schedule
from qiskit.pulse.exceptions import PulseError
from qiskit.pulse.schedule import ScheduleComponent

logger = logging.getLogger(__name__)


class PasqalSchedule(Schedule):
    """A quantum program *schedule* with exact time constraints for its instructions, operating
    over all input signal *channels* and supporting special syntaxes for building.

    Pulse program representation for Pasqal'a analog Neutral Atom processors.
    """

    def __init__(
        self,
        *schedules: Schedule | Instruction | tuple[int, Schedule | Instruction],
        register: Register,
        name: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        if isinstance(metadata, dict):
            metadata["register"] = register
        else:
            metadata: dict = {"register": register}  # type: ignore
        super().__init__(*schedules, name=name, metadata=metadata)

        self._register = register  # could just be set of coordinates

    @property
    def register(self) -> Register:
        """Register"""
        return self._register

    def _immutable_insert(
        self,
        start_time: int,
        schedule: "ScheduleComponent",
        name: str | None = None,
    ) -> "PasqalSchedule":
        """Return a new schedule with ``schedule`` inserted into ``self`` at ``start_time``.
        Args:
            start_time: Time to insert the schedule.
            schedule: Schedule to insert.
            name: Name of the new ``Schedule``. Defaults to name of ``self``.
        """
        new_sched = PasqalSchedule.initialize_from(self, name)
        new_sched._mutable_insert(0, self)  # pylint: disable=protected-access
        new_sched._mutable_insert(  # pylint: disable=protected-access
            start_time, schedule
        )
        return new_sched

    def _immutable_shift(self, time: int, name: str | None = None) -> "PasqalSchedule":
        """Return a new schedule shifted forward by `time`.

        Args:
            time: Time to shift by
            name: Name of the new schedule if call was mutable. Defaults to name of self
        """
        shift_sched = PasqalSchedule.initialize_from(self, name)
        shift_sched.insert(time, self, inplace=True)

        return shift_sched

    def replace(
        self,
        old: "ScheduleComponent",
        new: "ScheduleComponent",
        inplace: bool = False,
    ) -> "PasqalSchedule":
        """Return a ``Schedule`` with the ``old`` instruction replaced with a ``new``
        instruction.

        The replacement matching is based on an instruction equality check.

        .. code-block::

            from qiskit import pulse

            d0 = pulse.DriveChannel(0)

            sched = pulse.Schedule()

            old = pulse.Play(pulse.Constant(100, 1.0), d0)
            new = pulse.Play(pulse.Constant(100, 0.1), d0)

            sched += old

            sched = sched.replace(old, new)

            assert sched == pulse.Schedule(new)

        Only matches at the top-level of the schedule tree. If you wish to
        perform this replacement over all instructions in the schedule tree.
        Flatten the schedule prior to running::

        .. code-block::

            sched = pulse.Schedule()

            sched += pulse.Schedule(old)

            sched = sched.replace(old, new)

            assert sched == pulse.Schedule(new)

        Args:
            old: Instruction to replace.
            new: Instruction to replace with.
            inplace: Replace instruction by mutably modifying this ``Schedule``.

        Returns:
            The modified schedule with ``old`` replaced by ``new``.

        Raises:
            PulseError: If the ``Schedule`` after replacements will has a timing overlap.
        """
        # pylint:disable-next=import-outside-toplevel
        from qiskit.pulse.parameter_manager import ParameterManager

        if inplace:
            return super().replace(old, new, inplace)

        new_children = []
        new_parameters = ParameterManager()

        for time, child in self.children:
            if child == old:
                new_children.append((time, new))
                new_parameters.update_parameter_table(new)
            else:
                new_children.append((time, child))
                new_parameters.update_parameter_table(child)
        try:
            new_sched = PasqalSchedule.initialize_from(self)
            for time, inst in new_children:
                new_sched.insert(time, inst, inplace=True)
            return new_sched
        except PulseError as err:
            raise PulseError(
                f"Replacement of {old} with {new} results in overlapping instructions."
            ) from err

    @classmethod
    def initialize_from(
        cls, other_program: Any, name: str | None = None
    ) -> "PasqalSchedule":
        """Create new schedule object with metadata of another schedule object.

        Args:
            other_program: Qiskit program that provides metadata to new object.
            name: Name of new schedule. Name of ``schedule`` is used by default.

        Returns:
            New schedule object with name and metadata.

        Raises:
            PulseError: When `other_program` does not provide necessary information.
        """
        try:
            name = name or other_program.name

            if other_program.metadata:
                metadata = other_program.metadata.copy()
            else:
                metadata = None

            register = copy(other_program.register)

            return cls(name=name, register=register, metadata=metadata)
        except AttributeError as ex:
            raise PulseError(
                f"{cls.__name__} cannot be initialized from the program data "
                f"{other_program.__class__.__name__}."
            ) from ex
