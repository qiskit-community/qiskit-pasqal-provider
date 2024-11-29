"""Unit tests for converting Schedules to Pulser Sequences"""

from unittest import TestCase

import pulser
from qiskit.pulse import Constant, DriveChannel, Gaussian, Play, Schedule

from qiskit_pasqal_provider.providers.pasqal_utils import to_pulser


class TestConversion(TestCase):
    """Tests prototype template."""

    def test_schedule_conversion(self):
        """Tests conversion of Qiskit pulse schedule to Pulser sequence."""
        sched1 = Schedule()

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

        pulser_sequence = to_pulser(sched)

        assert pulser_sequence
        assert isinstance(pulser_sequence, pulser.Sequence)
        assert pulser_sequence.get_duration() == 200
        assert pulser_sequence.get_register()  # todo, program and validate
