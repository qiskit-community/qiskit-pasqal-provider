"""Unit tests for converting Schedules to Pulser Sequences"""

from unittest import TestCase

import pulser
import pytest
import qiskit
from qiskit.pulse import Constant, DriveChannel, Play, Schedule

from qiskit_pasqal_provider.providers.pasqal_schedule import PasqalSchedule
from qiskit_pasqal_provider.providers.pasqal_utils import to_pulser


class TestConversion(TestCase):
    """Tests prototype template."""

    def test_schedule_conversion(self):
        """Tests conversion of Qiskit pulse schedule to Pulser sequence."""
        register = pulser.Register.rectangle(1, 4, spacing=5, prefix="atom")
        sched1 = PasqalSchedule(register=register)
        # Easy option: one DriveChannel for Global Rabi and one for Detuning
        # Units are nanoseconds and rad/us, phase
        # limit_amplitude=False, default is True -> limit norm to 1
        sched1 += Play(
            Constant(
                duration=200, amp=2, angle=1.57, name="rabi", limit_amplitude=False
            ),
            DriveChannel(0),
        )

        sched2 = Schedule()
        sched2 += Play(
            Constant(200, -10, name="detuning", limit_amplitude=False), DriveChannel(1)
        )
        sched = sched1 | sched2
        pulser_sequence = to_pulser(sched, pulser.AnalogDevice)

        assert pulser_sequence
        assert isinstance(pulser_sequence, pulser.Sequence)
        assert pulser_sequence.get_duration() == 200
        assert pulser_sequence.get_register()  # todo, program and validate


class TestScheduleConstruction(TestCase):
    """Tests prototype template."""

    def test_schedule_construction(self):
        """Tests contstructions of Qiskit pulse schedule."""
        register = pulser.Register.rectangle(1, 4, spacing=5, prefix="atom")
        sched1 = PasqalSchedule(register=register)
        assert sched1.register
        assert sched1.metadata["register"] == sched1.register
        assert isinstance(sched1, Schedule)
        # Easy option: one DriveChannel for Global Rabi and one for Detuning
        # Units are nanoseconds and rad/us, phase
        # limit_amplitude=False, default is True -> limit norm to 1
        sched1 += Play(
            Constant(
                duration=200, amp=2, angle=1.57, name="rabi", limit_amplitude=False
            ),
            DriveChannel(0),
        )
        assert sched1.register

        sched2 = Schedule()
        sched2 += Play(
            Constant(200, -10, name="detuning", limit_amplitude=False), DriveChannel(1)
        )

        # Compose a PasqalSchedule with Register first, OK
        sched = sched1 | sched2
        assert sched1.metadata["register"] == sched1.register
        assert sched.register == sched1.register

        # Not OK, overlapping channels at the same time
        # need to decide if create new channels or what to do here
        with pytest.raises(qiskit.pulse.exceptions.PulseError):
            sched.replace(sched1, sched2)

        # Not OK, Schedule first and PasqalSchedule with Register second
        sched = sched2 | sched1
        with pytest.raises(AttributeError):
            assert sched.register  # pylint: disable=no-member
        with pytest.raises(KeyError):
            assert sched.metadata["register"]
