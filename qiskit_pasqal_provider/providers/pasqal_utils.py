"""Pasqal backend utilities"""

from dataclasses import dataclass

import pulser
import qiskit
from qiskit.pulse import Constant, Schedule, Play
from qiskit.pulse.channels import PulseChannel
from qiskit.pulse.library.pulse import Pulse


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


class TwoPhotonSchedule(Schedule):
    """
    Schedule class that holds 2 pulses (rabi, detuning) suitable for Neutral Atom Analog devices.
    """

    def __init__(
        self,
        channel: PulseChannel,
        rabi: Pulse | None = None,
        detuning: Pulse | None = None,
        name: str | None = None,
        metadata: dict | None = None,
    ):
        schedules = [
            Play(rabi, channel=channel, name=rabi.name or "rabi"),
            Play(detuning, channel=channel, name=detuning.name or "detuning"),
        ]
        super().__init__(*schedules, name=name, metadata=metadata)


def to_pulser(sched: Schedule) -> list[tuple[pulser.Pulse, str]]:
    """Utility function to convert a Qiskit Pulse Schedule into a Pulser Sequence."""

    # Set up default register in here until we figure out how to expose this
    # API in the Qiskit interface. A Register can take predefined shapes, or
    # be defined from co-ordinates.
    # Here we define 4 atoms on a line 4 um apart
    # reg = pulser.Register.rectangle(1, 4, spacing=5, prefix="atom")

    # # Initialise the sequence and channel
    # seq = pulser.Sequence(reg, pulser.AnalogDevice)
    # seq.declare_channel("rydberg_global", "rydberg_global")

    # Everything above this can perhaps be moved to the PasqalBackend?

    pulses: dict[int, TwoPhotonPulse] = {}
    for time, instruction in sched.instructions:
        if not isinstance(instruction, qiskit.pulse.Play):
            raise NotImplementedError

        _pulse = instruction.pulse
        pulse = pulses.get(
            time,
            TwoPhotonPulse(time=time, duration=_pulse.duration, phase=_pulse.angle),
            # resolve how to get phase from qiskit.pulse.Play.Pulse object
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

    # Form final Pulser pulse from the two constituents and the phase angle.
    pulser_pulses = [
        (pulser.Pulse(pulse.rabi, pulse.detuning, phase=pulse.phase), "rydberg_global")
        for time, pulse in pulses.items()
    ]
    return pulser_pulses
