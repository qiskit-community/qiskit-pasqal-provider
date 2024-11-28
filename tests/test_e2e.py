"""End to end tests running qiskit composed programs on Pasqal backends"""

from unittest import TestCase

from qiskit.pulse import Constant, DriveChannel, Gaussian, Play, Schedule

from qiskit_pasqal_provider.providers.pasqal_backend import PasqalLocalBackend


class TestPrototypeTemplate(TestCase):
    """Tests prototype template."""

    def test_template_class(self):
        """Tests template class."""
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

        bknd = PasqalLocalBackend()
        job = bknd.run(sched)
        job.submit()
        res = job.result()
        counts = res.get_counts()
        assert counts
        print(counts)
