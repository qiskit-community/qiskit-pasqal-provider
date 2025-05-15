"""Pasqal backend utilities"""

from dataclasses import dataclass

from typing import Literal
import numpy as np
from numpy.typing import ArrayLike
import pulser
from pulser import Sequence, Pulse
from pulser.devices._device_datacls import BaseDevice
from pulser.parametrized import Variable, ParamObj, Parametrized
from pulser.register import Register
from pulser.waveforms import InterpolatedWaveform
from qiskit.circuit import QuantumCircuit, ParameterExpression, Parameter

from qiskit_pasqal_provider.providers.target import PasqalDevice


# defining handy type aliases
GridLiteralType = Literal["linear", "triangular", "square"]
CoordsType = ArrayLike | list[ArrayLike] | tuple[ArrayLike]


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


def _get_wf_values(
    seq: Sequence, values: int | float | Parameter | ArrayLike
) -> ParamObj | int | float | Variable | None:
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
            return values

        case tuple() | list() | np.ndarray():

            if all(isinstance(k, Parameter) for k in values) and len(set(values)) == 1:
                var = seq.declare_variable(values[0].name, size=len(values), dtype=float)
                return var

            new_values = ()

            for value in values:
                res = _get_wf_values(seq, value)

                if res is not None:
                    new_values += res,

            return new_values[0] if len(new_values) == 1 else new_values

        case np.integer() | np.floating():
            return values

        case Parameter():
            if values.name not in seq.declared_variables:
                # single parameters must be of size 1
                var = seq.declare_variable(values.name, size=1, dtype=float)
                return var

            return None

        case ParameterExpression():
            raise NotImplementedError(
                "Current Pasqal provider version does not support parametric expressions."
            )

        case None:
            return None

        case _:
            raise NotImplementedError(f"values {type(values)} not supported.")


def gen_seq(
    analog_register: PasqalRegister,
    device: BaseDevice | PasqalDevice,
    circuit: QuantumCircuit,
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

    for instr in circuit.data:
        # gate.operation must be an analog gate
        gate = instr.operation

        if (
            hasattr(gate, "amplitude")
            and hasattr(gate, "detuning")
            and hasattr(gate, "phase")
        ):
            amp_wf = InterpolatedWaveform(
                duration=gate.amplitude.duration,
                values=_get_wf_values(seq, gate.amplitude.values),
                times=_get_wf_values(seq, gate.amplitude.times) or None,
                interpolator=gate.amplitude.interpolator,
                **gate.amplitude.interpolator_options,
            )

            det_wf = InterpolatedWaveform(
                duration=gate.detuning.duration,
                values=_get_wf_values(seq, gate.detuning.values),
                times=_get_wf_values(seq, gate.detuning.times) or None,
                interpolator=gate.detuning.interpolator,
                **gate.detuning.interpolator_options,
            )

            # phase should be a scalar (at least that's what we have in `pulser.Pulse`)
            pulse = Pulse(amp_wf, det_wf, gate.phase)

            seq.add(pulse, channel_name)

        else:
            raise ValueError(
                f"gate {gate} has no waveform properties and "
                "therefore cannot be used for analog computing."
            )

    assert isinstance(seq, Sequence)

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

        if hasattr(gate.operation, "analog_register"):
            registers.append(gate.operation.analog_register)

        else:
            raise ValueError("'run_input' argument must only contain analog gate.")

    # for now, it does not support multiple analog gates and multiple registers
    if len(registers) > 1:
        raise ValueError(
            "Pasqal's QPU backend supports only a single analog gate with one coordinates set"
        )

    return registers[0]


class RegisterTransform:
    """Transforms register data according to the `grid_type`."""

    _grid: GridLiteralType
    _grid_scale: float
    _raw_coords: CoordsType
    coords: CoordsType

    # Below is a multiplying factor that seems to be needed to correct the values coming from
    # the user's coords definition. It should be used on the coordinate transformations.
    scale_factor: int = 5

    def __init__(
        self,
        grid_transform: GridLiteralType | None,
        grid_scale: float = 1.0,
        coords: list[tuple[int, int]] | None = None,
        num_qubits: int | None = None,
    ):
        """
        Args:
            grid_transform (Literal["linear", "triangular", "square"], None): literal str to choose
                which grid transform to use. Accepted values are "linear", "triangular"
                or "square". If None is provided, it will default to "triangular"
            grid_scale (float): scale of the grid. Default is `1.0`
            coords (list[tuple[int, int]]): list of coordinates as qubit positions in an int
                grid, e.g. `[(0, 0), (1, 0), (0, 1)]`. Default is `None`
            num_qubits (int | None): number of qubits as integer. Default is `None`
        """

        self._grid = grid_transform if grid_transform is not None else "triangular"
        self._grid_scale = grid_scale

        # defining self.raw_coords
        if coords:
            self._raw_coords = coords

        elif num_qubits:
            self._raw_coords = self._fill_coords(num_qubits)

        else:
            raise ValueError("must provide coords or num_qubits.")

        # applying the appropriate method to transform self.raw_coords
        try:
            self.coords = getattr(self, f"_{self._grid}_coords")()

        except AttributeError:
            self.invalid_grid_value()

    @property
    def raw_coords(self) -> CoordsType:
        """Original coordinates"""
        return self._raw_coords

    @classmethod
    def _fill_coords(cls, num_qubits: int) -> list[tuple[int, int]]:
        shift = num_qubits // 2
        return [(p - shift, 0) for p in range(num_qubits)]

    @classmethod
    def invalid_grid_value(cls) -> None:
        """Fallback function for invalid `grid_transform` value."""

        raise ValueError(
            "grid_transform should be 'linear', 'triangular', or 'square'."
        )

    def _linear_coords(self) -> np.ndarray:
        """
        Transforms coordinates into linear coordinates.

        Returns:
            np.ndarray of transformed coordinates.
        """

        raise NotImplementedError()

    def _triangular_coords(self) -> np.ndarray:
        """
        Transforms coordinates into triangular coordinates.

        Returns:
            np.ndarray of transformed coordinates
        """

        # triangular transformation matrix
        transform = np.array([[1.0, 0.0], [0.5, 0.8660254037844386]])
        return (
            np.array(self._raw_coords)
            * self._grid_scale
            * self.scale_factor
            @ transform
        )

    def _square_coords(self) -> np.ndarray:
        """
        Transforms coordinates into square coordinates.

        Returns:
            np.ndarray of transformed coordinates
        """

        # for now, no transformation needed since the coords are list of tuple of ints
        return np.array(self._raw_coords) * self._grid_scale * self.scale_factor
