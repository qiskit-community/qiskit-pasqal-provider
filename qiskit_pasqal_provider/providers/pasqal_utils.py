"""Pasqal backend utilities"""

from dataclasses import dataclass

import pulser
import qiskit
from qiskit.pulse import Constant, Schedule


@dataclass
class TwoPhotonPulse:
    """Dataclass holding the two different waveform objects for amplitude/rabi and
    detuning that together constitute a Neutral Atom Analog Pulse Sequence.
    """

    time: int = 0
    duration: int = 0
    rabi: pulser.waveforms.Waveform = None
    detuning: pulser.waveforms.Waveform = None
    phase: float = 0


def to_pulser(sched: Schedule) -> pulser.Sequence:
    """Utility function to convert a Qiskit Pulse Schedule into a Pulser Sequence."""

    # Set up default register in here until we figure out how to expose this
    # API in the Qiskit interface. A Register can take predefined shapes, or
    # be defined from co-ordinates.
    # Here we define 4 atoms on a line 4 um apart
    reg = pulser.Register.rectangle(1, 4, spacing=5, prefix="atom")

    # Initialise the sequence and channel
    seq = pulser.Sequence(reg, pulser.AnalogDevice)
    seq.declare_channel("rydberg_global", "rydberg_global")

    # Everything above this can perhaps be moved to the PasqalBackend?

    pulses: dict[int, TwoPhotonPulse] = {}
    for time, instruction in sched.instructions:
        if not isinstance(instruction, qiskit.pulse.Play):
            raise NotImplementedError

        _pulse = instruction.pulse
        pulse = pulses.get(
            time,
            TwoPhotonPulse(time=time, duration=_pulse.duration, phase=_pulse.angle),
        )

        # maybe a solution will be to implement specific channel for Neutral-Atoms
        # or "global", currently encoding into name of instruction manually when defining
        # channel = instruction.channel
        # qubit_index = channel.index
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
        # Form final Pulser pulse from the two constituents and the phase angle.
        _pulse = pulser.Pulse(pulse.rabi, pulse.detuning, phase=pulse.phase)
        seq.add(_pulse, "rydberg_global")
    return seq
