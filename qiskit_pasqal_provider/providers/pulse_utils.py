"""Pasqal backend utilities"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike
import pulser
from pulser import Sequence, Pulse
from pulser.parametrized import Variable
from pulser.register import Register
from pulser.waveforms import InterpolatedWaveform
import qiskit
from qiskit.circuit import QuantumCircuit, ParameterExpression, Parameter
from qiskit.pulse import Constant, Schedule

from qiskit_pasqal_provider.providers.target import PasqalDevice


class PasqalRegister(Register):
    """PasqalRegister class. To define a register for the PasqalBackend run method"""


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


# todo: refactor `to_pulser` to accommodate `HamiltonianGate` operation
def to_pulser(sched: Schedule) -> list[tuple[pulser.Pulse, str]]:
    """Utility function to convert a Qiskit Pulse Schedule into a Pulser Sequence."""

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

    # Form final Pulser pulse from the two constituents and the phase angle.
    pulser_pulses = [
        (pulser.Pulse(pulse.rabi, pulse.detuning, phase=pulse.phase), "rydberg_global")
        for time, pulse in pulses.items()
    ]
    return pulser_pulses


def _get_wf_values(
    seq: Sequence, values: int | float | Parameter | ArrayLike
) -> tuple[int | float | Variable]:
    """
    Get waveform parameters to transform into number or pulser parametric variable. For now,
    it is assumed that parametric values are single-sized.

    Args:
        seq: A pulser Sequence.
        values: int, float, qiskit Parameter or an array-like object.

    Returns:
        A tuple containing the python base type values.
    """

    match values:

        case int() | float():
            return (values,)

        case list() | tuple() | np.ndarray():
            new_values = ()
            for value in values:
                new_values += _get_wf_values(seq, value)

            return new_values

        case Parameter():
            # for now, parameter will be of size 1
            var = seq.declare_variable(values.name, size=1, dtype=float)
            return (var,)

        case ParameterExpression():
            raise NotImplementedError(
                "Current Pasqal provider version does not support parametric expressions."
            )

        case _:
            raise NotImplementedError(f"values {type(values)} not supported.")


def gen_seq(
    analog_register: PasqalRegister, device: PasqalDevice, circuit: QuantumCircuit
) -> Sequence:
    """
    Generate a sequence for a given analog_register (PasqalRegister), device (PasqalDevice)
    and circuit (qiskit.QuantumCircuit).

    Args:
        analog_register: a PasqalRegister instance.
        device: a PasqalDevice instance.
        circuit: a qiskit QuantumCircuit instance.

    Returns:
        The pulser sequence containing the converted analog gate from the quantum circuit.
    """

    # make channel_name a function argument if it varies throughout devices
    channel_name = "rydberg_global"
    seq = Sequence(analog_register, device)
    seq.declare_channel(channel_name, channel_name)

    for gate in circuit.data:
        # gate must be an analog gate
        if (
            hasattr(gate, "_amplitude")
            and hasattr(gate, "_detuning")
            and hasattr(gate, "_phase")
        ):
            amp_wf = InterpolatedWaveform(
                duration=gate._amplitude.duration,
                values=_get_wf_values(seq, gate._amplitude.values),
                interpolator=gate._amplitude._interpolator,
                **gate._amplitude._interpolator_kwargs,
            )

            det_wf = InterpolatedWaveform(
                duration=gate._detuning.duration,
                values=_get_wf_values(seq, gate._detuning.values),
                interpolator=gate._detuning._interpolator,
                **gate._detuning._interpolator_kwargs,
            )

            # phase should be a scalar (at least that's what we have in `pulser.Pulse`
            pulse = Pulse(amp_wf, det_wf, gate._phase)

            seq.add(pulse, channel_name)

        else:
            raise ValueError(
                f"gate {gate} has no waveform properties and "
                f"therefore cannot be used for analog computing."
            )

    return seq


def get_register_from_circuit(run_input: QuantumCircuit) -> PasqalRegister:
    """
    Get the analog register (`PasqalRegister`) from the given circuit.

    Args:
        run_input: the QuantumCircuit

    Returns:
        The PasqalRegister instance.
    """

    # get the analog_register from the analog gate
    registers = []
    for gate in run_input.data:

        if hasattr(gate, "analog_register"):
            registers.append(gate.analog_register)

        else:
            raise ValueError("'run_input' argument must only contain analog gate.")

    # for now, it does not support multiple analog gates and multiple registers
    if len(registers) > 1:
        raise ValueError(
            "Pasqal's QPU backend supports only a single analog gate with one coordinates set"
        )

    return registers[0]
