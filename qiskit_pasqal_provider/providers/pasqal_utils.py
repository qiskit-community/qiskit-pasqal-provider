"""Pasqal backend utilities"""

from dataclasses import dataclass

import pulser
import qiskit
from qiskit.pulse import Constant, Schedule


@dataclass
class TwoPhotonPulse:
    time: int = 0
    duration: int = 0
    rabi: pulser.waveforms.Waveform = None
    detuning: pulser.Pulse = None
    phase: float = 0


def to_pulser(sched: Schedule) -> pulser.Sequence:
    # TODO, convert from Schedule...
    reg = pulser.Register.rectangle(1, 2, spacing=8, prefix="atom")
    seq = pulser.Sequence(reg, pulser.AnalogDevice)
    seq.declare_channel("rydberg_global", "rydberg_global")
    pulses: dict[int, TwoPhotonPulse] = {}
    for time, instruction in sched.instructions:
        if not isinstance(instruction, qiskit.pulse.Play):  # type: ignore
            raise NotImplementedError

        _pulse = instruction.pulse
        pulse = pulses.get(
            time,
            TwoPhotonPulse(time=time, duration=_pulse.duration, phase=_pulse.angle),
        )

        # TODO: maybe a solution will be to implement specific channel for Neutral-Atoms
        # or "global", currently encoding into name of instruction manually when defining

        channel = instruction.channel
        qubit_index = channel.index
        name = instruction.name
        if isinstance(_pulse, Constant):
            if name == "rabi":  # or use the channel 0 for amp, 1 for det e.g.
                pulse.rabi = pulser.ConstantWaveform(_pulse.duration, _pulse.amp)
            elif name == "detuning":
                pulse.detuning = pulser.ConstantWaveform(_pulse.duration, _pulse.amp)
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError("Currently only constant pulses")
        pulses[time] = pulse
    for time, pulse in pulses.items():
        _pulse = pulser.Pulse(pulse.rabi, pulse.detuning, phase=pulse.phase)
        seq.add(_pulse, "rydberg_global")
    return seq
