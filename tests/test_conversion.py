"""Unit tests for converting Schedules to Pulser Sequences"""

import pulser
from qiskit.pulse import Constant, DriveChannel, Play, Schedule

from qiskit_pasqal_provider.providers.pasqal_utils import to_pulser


def test_schedule_conversion(
    pasqal_register: pulser.Register,
    pasqal_device: pulser.devices.Device,
):
    """Tests conversion of Qiskit pulse schedule to Pulser sequence."""
    sched1 = Schedule()

    # Easy option: one DriveChannel for Global Rabi and one for Detuning
    # Units are nanoseconds and rad/us, phase
    # limit_amplitude=False, default is True -> limit norm to 1
    sched1 += Play(
        Constant(duration=200, amp=2, angle=1.57, name="rabi", limit_amplitude=False),
        DriveChannel(0),
    )

    sched2 = Schedule()
    sched2 += Play(
        Constant(200, -10, name="detuning", limit_amplitude=False), DriveChannel(1)
    )
    sched = sched1 | sched2

    pulser_pulses = to_pulser(sched)
    assert pulser_pulses
    assert len(pulser_pulses) == 1

    seq = pulser.Sequence(register=pasqal_register, device=pasqal_device)
    seq.declare_channel("rydberg_global", "rydberg_global")

    for pulse, channel in pulser_pulses:
        seq.add(pulse, channel)

    assert seq.get_duration() == 200
    assert seq.get_register()  # todo, program and validate
