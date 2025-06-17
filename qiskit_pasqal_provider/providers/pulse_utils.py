"""Pasqal backend utilities"""

from dataclasses import dataclass
from functools import reduce

from typing import Any, Literal
import numpy as np
import pulser
from pulser import Sequence, Pulse
from pulser.devices._device_datacls import BaseDevice
from pulser.parametrized import Variable, ParamObj
from pulser.register import Register
from pulser.waveforms import InterpolatedWaveform, CustomWaveform, Waveform
from qiskit.circuit import QuantumCircuit, ParameterExpression, Parameter

from qiskit_pasqal_provider.providers.target import PasqalDevice


# defining handy type aliases
GridLiteralType = Literal["linear", "triangular", "square"]
CoordsType = list | tuple | np.ndarray | tuple[tuple[int | float ], ...]


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
        values: list | tuple | np.ndarray | ParameterExpression,
        duration: int | float | ParameterExpression = 1000,
        times: list | tuple | np.ndarray | None = None,
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
            values = (
                values if isinstance(values, list | tuple | np.ndarray) else [values]
            )
            n = len(values)

        elif isinstance(values, ParameterExpression) and None is not n:
            values = [values for _ in range(n)]

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
    def values(self) -> list | tuple | np.ndarray:
        """data points for interpolation"""
        return self._values

    @property
    def times(self) -> list | tuple | np.ndarray | None:
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
        for k in self.values:
            if isinstance(k, Parameter | ParameterExpression):
                values_params.extend(k.parameters)

        duration_params = (
            list(self.duration.parameters)
            if isinstance(self.duration, ParameterExpression)
            else []
        )

        times_params = []

        if self.times is not None:
            for k in self.times:
                if isinstance(k, Parameter | ParameterExpression):
                    times_params.extend(k.parameters)

        return list(set(values_params + duration_params + times_params))

    def __len__(self) -> int:
        """InterpolatePoints length is equal to its values' length."""
        return len(self.values)


class ParamCustomWaveform(ParamObj):
    """
    Parametrized custom waveform class. To be used when parametrizing custom
    waveform is needed.
    """

    def __init__(
        self,
        amp_wf: Waveform | ParamObj,
        det_wf: Waveform | ParamObj,
        phase_wf: Waveform | ParamObj,
    ):
        """
        Parametrizing custom waveform based on detuning waveforms and phase
        pulses/parametric objects.

        Args:
            amp_wf: a pulser Waveform or ParamObj object
            det_wf: a pulser Waveform or ParamObj object
            phase: a pulser Waveform or ParamObj object
        """

        self._amp_wf = amp_wf
        self._det_wf = det_wf
        self._phase_wf = phase_wf
        self._phase_mod = Pulse.ArbitraryPhase(self._amp_wf, self._phase_wf)

        variables: dict = {}

        if isinstance(det_wf, ParamObj):
            variables.update(det_wf.variables)

        if isinstance(phase_wf, ParamObj):
            variables.update(phase_wf.variables)

        super().__init__(
            CustomWaveform,
            samples=[0, 1],
            # vars=variables
        )

    @property
    def phase_mod(self) -> Pulse | None:
        """Phase modulation. Optional"""
        return self._phase_mod

    def build(self) -> Any:
        """Builds the object with its variables last assigned values."""

        det_obj = (
            self._det_wf.build() if isinstance(self._det_wf, ParamObj) else self._det_wf
        )

        # if isinstance(self._phase_wf, ParamObj):
        #     phase_obj = self._phase_wf.build()
        #
        # else:
        #     phase_obj = self._phase_wf
        #

        self._phase_mod = (
            self._phase_mod.build()
            if isinstance(self._phase_mod, ParamObj)
            else self._phase_mod
        )

        self.kwargs["samples"] = det_obj.samples + self._phase_mod.detuning.samples

        if "vars" in self.kwargs:
            self.kwargs.pop("vars")

        return super().build()


class ObjWrapper:
    """Object wrapper class. Used for wrapping `pulser` `Variable` and array-like objects."""

    def __init__(self, var: Variable | tuple | None, value: np.ndarray | tuple | None):
        """
        A wrapper class to handle parametric and array-like data.

        Args:
            var: a `pulser`'s `Variable` object to represent parametric data. Can be None.
            value: an array-like object to represent non-parametric data. Can be None.
        """

        self._var = var if isinstance(var, Variable) else ()
        self._value = value if isinstance(var, np.ndarray | tuple) else ()

        lsize = var.size if isinstance(var, np.ndarray | Variable) else len(var)
        rsize = value.size if isinstance(value, np.ndarray | Variable) else len(value)

        self._size = lsize or rsize
        self._data = self._var if not isinstance(self._var, tuple) else self._value

    @property
    def var(self) -> Variable | None | tuple:
        """Variable data"""
        return self._var

    @property
    def value(self) -> np.ndarray | tuple[Any, ...] | tuple:
        """Value data (array-like)"""
        return self._value

    @property
    def data(self) -> tuple[Any, ...] | Variable | np.ndarray:
        """A non-empty data, from either var or value attributes class"""
        return self._data

    @property
    def size(self) -> int:
        """Size of the non-empty data"""
        return self._size


def _gen_phase_pulse(
    seq: Sequence,
    duration: int | float | Variable,
    ampl_wf: InterpolatedWaveform,
    phase: InterpolatePoints,
    det_wrapper: ObjWrapper,
) -> Pulse:
    """
    Get phase and transform into a waveform, with a new detuning from the two sources.
    Either `det_var` or `det_values` must be present, but not both.

    Args:
        seq: the pulse Sequence object.
        ampl_wf: amplitude waveform (InterpolatedWaveform).
        det_wrapper: ObjWrapper object for detuning waveforms containing either pulser
            Variables or array-like data
        phase: phase (either InterpolatePoints, float or ParameterExpression).
        duration: float or pulser.parametrized.Variable.

    Returns:
        A parametric pulse with the phase InterpolatedWaveform containing detuning Variables.
    """

    phase_wrapper = _get_param_values(seq, phase.values, True)  # type: ignore [arg-type]

    phase_wf = _gen_phase_wf(
        det_wrapper,
        phase_wrapper,
        duration=duration,
        times=phase.times,
        interpolator=phase.interpolator,
        **phase.interpolator_options,
    )

    # Use a phase modulated pulse to calculate the corresponding
    # detuning waveform and phase offset of phase_wf
    return pulser.Pulse.ArbitraryPhase(ampl_wf, phase_wf)


def _gen_phase_wf(
    *values: ObjWrapper,
    duration: int | float | Variable,
    times: list | tuple | np.ndarray | None,
    interpolator: str,
    **interpolator_kwargs: Any,
) -> InterpolatedWaveform:
    """
    Generate phase waveform from ObjWrapper data (parametric or array-like data)
    and waveform data such as duration, times and interpolator.

    Args:
        *values: ObjWrapper data to build the phase waveform (usually detuning and phase values).
        duration: phase waveform duration.
        times: array-like data to build the waveform time series.
        interpolator: SciPy interpolation class to use.
        **interpolator_kwargs: extra parameters to give to the chosen interpolator class.

    Returns:
        An InterpolatedWaveform object for the phase waveform, given detuning and phase data.
    """

    new_values = reduce(lambda x, y: x + y.data, values[1:], values[0].data)

    return InterpolatedWaveform(
        duration=duration,  # type: ignore [arg-type]
        values=new_values,
        times=times,
        interpolator=interpolator,
        **interpolator_kwargs,
    )


def _get_wf_values(
    seq: Sequence, values: int | float | Parameter | list | tuple | np.ndarray
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

            # check if parameter is unique
            if all(isinstance(k, Parameter) for k in values) and len(set(values)) == 1:
                if values[0].name not in seq.declared_variables:
                    var = seq.declare_variable(
                        values[0].name, size=len(values), dtype=float
                    )
                    return var

                return seq.declared_variables[values[0].name]

            # it may be an iterable of parameters
            new_values: (
                tuple[ParamObj | int | float | Variable | np.integer | np.floating]
                | tuple
            ) = ()

            # iterating over each element to retrieve the parameter(s)
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
        gate = instr.operation

        # gate.operation must be an analog gate
        assert (
            hasattr(gate, "amplitude")
            and hasattr(gate, "detuning")
            and hasattr(gate, "phase")
        ), (
            f"gate {gate} has no waveform properties and therefore cannot"
            f" be used for analog computing."
        )

        amp_duration = _get_wf_values(seq, gate.amplitude.duration)

        amp_wf = InterpolatedWaveform(
            duration=amp_duration,  # type: ignore [arg-type]
            values=_get_wf_values(seq, gate.amplitude.values),
            times=_get_wf_values(seq, gate.amplitude.times) or None,
            interpolator=gate.amplitude.interpolator,
            **gate.amplitude.interpolator_options,
        )

        det_duration = _get_wf_values(seq, gate.detuning.duration)
        det_values = _get_wf_values(seq, gate.detuning.values)

        det_wf = InterpolatedWaveform(
            duration=det_duration,  # type: ignore [arg-type]
            values=det_values,
            times=_get_wf_values(seq, gate.detuning.times) or None,
            interpolator=gate.detuning.interpolator,
            **gate.detuning.interpolator_options,
        )

        if isinstance(gate.phase, float):
            # in case phase is scalar
            phase = gate.phase
            pulse = Pulse(amp_wf, det_wf, phase)

        else:
            # otherwise, it's InterpolatePoints
            det_wrapper = _get_param_values(seq, det_values)  # type: ignore [arg-type]

            pulse = _gen_phase_pulse(
                seq=seq,
                duration=amp_duration,  # type: ignore [arg-type]
                ampl_wf=amp_wf,
                phase=gate.phase,
                det_wrapper=det_wrapper,
            )

        seq.add(pulse, channel_name)

    return seq


def _get_param_values(
    seq: Sequence,
    values: np.ndarray | tuple,
    check_wf: bool = False,
) -> ObjWrapper:
    """
    Retrieve parameters and values from a given InterpolatePoints object.

    Args:
        seq: a pulser Sequence object
        values: an iterable of elements to be sorted out as parameters or
            numeric values.

    Returns:
        An ObjWrapper instance containing parametric or non-parametric values.
    """

    wf_values = _get_wf_values(seq, values) if check_wf else values

    if isinstance(wf_values, Variable):
        return ObjWrapper(wf_values, ())

    return ObjWrapper((), wf_values)  # type: ignore [arg-type]


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
