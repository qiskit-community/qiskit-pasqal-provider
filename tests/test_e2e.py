"""End to end tests running qiskit composed programs on Pasqal backends"""

import pulser
import pytest
from qiskit.pulse import Constant, DriveChannel, Play

from qiskit_pasqal_provider.providers.pasqal_backend import PasqalLocalBackend
from qiskit_pasqal_provider.providers.pasqal_schedule import PasqalSchedule


@pytest.mark.parametrize("duration", [20, 100, 1000])
def test_e2e(duration: int) -> None:
    """Tests e2e the creation and execution of a pulse program on PasqalLocalBackend"""
    register = pulser.Register.rectangle(1, 4, spacing=5, prefix="atom")
    sched1 = PasqalSchedule(register=register)

    # Easy option: one DriveChannel for Global Rabi and one for Detuning
    # Units are nanoseconds and rad/us, phase
    # limit_amplitude=False, default is True -> limit norm to 1
    sched1 += Play(
        Constant(
            duration=duration, amp=2, angle=1.57, name="rabi", limit_amplitude=False
        ),
        DriveChannel(0),
    )

    sched2 = PasqalSchedule(register=register)
    sched2 += Play(
        Constant(duration=duration, amp=-10, name="detuning", limit_amplitude=False),
        DriveChannel(1),
    )

    sched3 = PasqalSchedule(register=register)
    sched3 += Play(
        Constant(duration=duration, amp=-10, name="detuning", limit_amplitude=False),
        DriveChannel(1),
    )
    sched4 = PasqalSchedule(register=register)
    sched4 += Play(
        Constant(
            duration=duration, amp=2, angle=1.57, name="rabi", limit_amplitude=False
        ),
        DriveChannel(0),
    )
    sched_0 = sched1 | sched2
    sched_1 = sched3 | sched4
    sched = sched_0 + sched_1
    bknd = PasqalLocalBackend(name="AnalogDevice")
    job = bknd.run(sched)
    job.submit()
    res = job.result()
    counts = res.get_counts()
    assert counts
