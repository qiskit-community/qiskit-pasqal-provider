"""End to end tests running qiskit composed programs on Pasqal backends"""

import pytest
from qiskit.pulse import Constant, DriveChannel, Play, Schedule

from qiskit_pasqal_provider.providers.pasqal_backend import PasqalLocalBackend
from qiskit_pasqal_provider.providers.pasqal_devices import PasqalTarget


@pytest.mark.parametrize("duration", [20, 100, 1000])
def test_e2e(duration: int, pasqal_target: PasqalTarget) -> None:
    """Tests e2e the creation and execution of a pulse program on PasqalLocalBackend"""

    sched1 = Schedule()

    # Easy option: one DriveChannel for Global Rabi and one for Detuning
    # Units are nanoseconds and rad/us, phase
    # limit_amplitude=False, default is True -> limit norm to 1
    sched1 += Play(
        Constant(
            duration=duration, amp=2, angle=1.57, name="rabi", limit_amplitude=False
        ),
        DriveChannel(0),
    )

    sched2 = Schedule()
    sched2 += Play(
        Constant(duration=duration, amp=-10, name="detuning", limit_amplitude=False),
        DriveChannel(1),
    )

    sched3 = Schedule()
    sched3 += Play(
        Constant(duration=duration, amp=-10, name="detuning", limit_amplitude=False),
        DriveChannel(1),
    )
    sched4 = Schedule()
    sched4 += Play(
        Constant(
            duration=duration, amp=2, angle=1.57, name="rabi", limit_amplitude=False
        ),
        DriveChannel(0),
    )
    sched_0 = sched1 | sched2
    sched_1 = sched3 | sched4
    sched = sched_0 + sched_1

    bknd = PasqalLocalBackend(target=pasqal_target, backend="qutip")
    job = bknd.run(sched)
    job.submit()
    res = job.result()
    counts = res.get_counts()
    assert counts
