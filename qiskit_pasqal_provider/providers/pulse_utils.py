"""Pasqal backend utilities"""

from dataclasses import dataclass

from typing import Literal, Any
import numpy as np
from numpy._typing import ArrayLike
from numpy.typing import ArrayLike
import pulser
from pulser import Sequence, Pulse
from pulser.devices._device_datacls import BaseDevice
from pulser.math.abstract_array import AbstractArray
from pulser.parametrized import Variable, ParamObj
from pulser.register import Register
from pulser.waveforms import InterpolatedWaveform, CustomWaveform
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


class InterpolatePoints:
    """
    A class to hold attributes for later use on `pulser`'s `InterpolateWaveform` class.
    It should be used to generate the points for the `HamiltonianGate` instance.
    """

    __slots__ = (
        "_values",
        "_duration",
        "_times",
        "_n",
        "_params",
        "_interpolator",
        "_interpolator_kwargs",
    )

    def __init__(
        self,
        values: ArrayLike | ParameterExpression,
        duration: int | float | ParameterExpression = 1000,
        times: ArrayLike | None = None,
        n: int | None = None,
        interpolator: str = "PchipInterpolator",
        **interpolator_kwargs: Any,
    ):
        """
        A class to hold attributes for later use on `pulser`'s `InterpolateWaveform`
        class. It should be used to generate the points for the `HamiltonianGate`
        instance.

        Args:
            values: an array-like data representing the points to be interpolated.
                It can be parametrized through `qiskit.circuit.Parameter`.
            duration: optional duration of the waveform (in ns). Defaults to 1000.
            times: Fractions of the total duration (between 0 and 1). Optional.
            n: the number of values points, in case `qiskit.circuit.Parameter` is
                provided on values argument. Default to None.
            interpolator: The SciPy interpolation class to use. Supports
                "PchipInterpolator" and "interp1d".
            **interpolator_kwargs: Extra parameters to give to the chosen
                interpolator class.
        """

        assert isinstance(duration, int | float | ParameterExpression)
        assert isinstance(interpolator, str)

        if n is None:
            values = np.array(values)
            n = len(values)

        elif isinstance(values, ParameterExpression) and None is not n:
            values = np.full(shape=n, fill_value=values)

        else:
            raise ValueError("Argument 'n' must be the size of values argument.")

        self._n = n
        self._values = values
        self._duration = duration
        self._times = times
        self._params = self._extract_params()
        self._interpolator = interpolator
        self._interpolator_kwargs = interpolator_kwargs

    @property
    def duration(self) -> int | float | Parameter:
        """duration of the waveform (in ns)"""
        return self._duration

    @property
    def values(self) -> ArrayLike:
        """data points for interpolation"""
        return self._values

    @property
    def times(self) -> ArrayLike | None:
        """normalized fraction of the total duration. Can be None"""
        return self._times

    @property
    def parameters(self) -> list[Parameter | ParameterExpression]:
        """list of parameters"""
        return self._params

    @property
    def interpolator(self) -> str:
        """The interpolator method name."""
        return self._interpolator

    @property
    def interpolator_options(self) -> dict:
        """The key-value pairs to fill the interpolator function with."""
        return self._interpolator_kwargs

    def _extract_params(self) -> list[Parameter | ParameterExpression]:
        """Extract the parameters list from values, duration and times arguments."""

        values_params = []
        for k in self.values:  # type: ignore [union-attr]
            if isinstance(k, Parameter | ParameterExpression):
                values_params.extend(k.parameters)

        duration_params = (
            list(self.duration.parameters)
            if isinstance(self.duration, ParameterExpression)
            else []
        )

        times_params = []

        if self.times is not None:
            for k in self.times:  # type: ignore [union-attr]
                if isinstance(k, Parameter | ParameterExpression):
                    times_params.extend(k.parameters)

        return list(set(values_params + duration_params + times_params))

    def __len__(self) -> int:
        """InterpolatePoints length is equal to its values' length."""
        return len(self.values)


def _get_phase(
    ampl_wf: InterpolatedWaveform,
    det_wf: InterpolatedWaveform,
    phase: float | InterpolatePoints | ParameterExpression,
    duration: int | float,
) -> tuple[CustomWaveform, AbstractArray]:
    """
    Get phase and transform into a waveform, with a new detuning from the two sources.

    Args:
        ampl_wf: amplitude waveform (InterpolatedWaveform).
        det_wf: detuning waveform (InterpolatedWaveform).
        phase: phase (either InterpolatePoints, float or ParameterExpression).
        duration: float

    Returns:
        A tuple containing the CustomWaveform made of the two-source detuning and a phase as array
    """

    # Pasqal's CUDA-Q `_setup_phase` function code used here
    # credits: Aleksander Wennersteen and Kaonan Micadei

    interpolator = "PchipInterpolator"

    # check phase type

    if isinstance(phase, InterpolatePoints):
        interpolator = phase.interpolator
        phases = phase.values
        times = (
            phase.times
            if phase.times is not None
            else np.linspace(0, 1, num=len(phase.values))
        )

    elif isinstance(phase, float):
        phases = [phase for _ in det_wf.samples]
        times = np.linspace(0, 1, num=len(det_wf.samples))

    elif isinstance(phase, Parameter):
        phases = [phase.name for _ in det_wf.samples]
        times = np.linspace(0, 1, num=len(det_wf.samples))

    else:
        raise ValueError(
            f"phase type is not supported for building pulses ({type(phase)});"
            f" must be InterpolatePoints, float or Parameter."
        )

    phase_wf = CustomWaveform(
        InterpolatedWaveform(
            duration,
            values=phases,
            times=times,
            interpolator=interpolator,
        ).samples  # type: ignore
    )
    # Use a phase modulated pulse to calculate the corresponding
    # detuning waveform and phase offset of phase_wf
    phase_mod = pulser.Pulse.ArbitraryPhase(ampl_wf, phase_wf)
    # Sum the detunings from the two sources
    full_det_wf = CustomWaveform(det_wf.samples + phase_mod.detuning.samples)
    # Extract the phase offset
    phase = phase_mod.phase

    return full_det_wf, phase  # type: ignore


def _get_wf_values(
    seq: Sequence, values: int | float | Parameter | ArrayLike
) -> ParamObj | int | float | Variable | np.integer | np.floating | tuple | None:
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
                var = seq.declare_variable(
                    values[0].name, size=len(values), dtype=float
                )
                return var

            new_values: (
                tuple[ParamObj | int | float | Variable | np.integer | np.floating]
                | tuple
            ) = ()

            for value in values:
                res = _get_wf_values(seq, value)

                if res is not None:
                    new_values += (res,)

            return new_values[0] if len(new_values) == 1 else new_values

        case np.integer() | np.floating():
            return values

        case Parameter():
            if values.name not in seq.declared_variables:
                # single parameters must be of size 1
                var = seq.declare_variable(values.name, size=1, dtype=float)
                return var

            return seq.declared_variables[values.name]

        case ParameterExpression():
            raise NotImplementedError(
                "Current Pasqal provider version does not support parametric expressions."
            )

        case None:
            return None

        case _:
            raise NotImplementedError(f"values {type(values)} not supported.")


def gen_seq(
    analog_register: PasqalRegister | Register,
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
                duration=_get_wf_values(seq, gate.amplitude.duration),
                values=_get_wf_values(seq, gate.amplitude.values),
                times=_get_wf_values(seq, gate.amplitude.times) or None,
                interpolator=gate.amplitude.interpolator,
                **gate.amplitude.interpolator_options,
            )

            det_wf = InterpolatedWaveform(
                duration=_get_wf_values(seq, gate.detuning.duration),
                values=_get_wf_values(seq, gate.detuning.values),
                times=_get_wf_values(seq, gate.detuning.times) or None,
                interpolator=gate.detuning.interpolator,
                **gate.detuning.interpolator_options,
            )

            if isinstance(gate.phase, float):
                # in case phase is scalar
                phase = gate.phase

            else:
                det_wf, phase = _get_phase(amp_wf, det_wf, gate.phase, amp_wf.duration)

            pulse = Pulse(amp_wf, det_wf, phase)

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
