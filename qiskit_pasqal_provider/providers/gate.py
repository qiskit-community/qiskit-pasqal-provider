"""Pasqal analog gate"""

from typing import Any, Union

import numpy as np
from numpy.typing import ArrayLike

from pulser.math import AbstractArray
from qiskit.circuit import Parameter, ParameterExpression
from qiskit.circuit.gate import Gate

from qiskit_pasqal_provider.providers.pulse_utils import (
    PasqalRegister,
    RegisterTransform,
    GridLiteralType,
)

CoordsKey = Union[str, int, float]


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

        elif isinstance(values, ParameterExpression) and None != n:
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


class HamiltonianGate(Gate):
    """Hamiltonian gate, an analog gate."""

    def __init__(
        self,
        amplitude: InterpolatePoints,
        detuning: InterpolatePoints,
        phase: float | ParameterExpression,
        coords: ArrayLike,
        grid_transform: GridLiteralType = "triangular",
        composed_wf: Any | None = None,
        transform: bool = False,
    ):
        """
        Hamiltonian gate is an analog gate that provides the relevant functionalities
        to use analog quantum computing in a circuit-like environment.

        Args:
            amplitude: an InterpolatePoints instance to represent an amplitude waveform.
            detuning: an InterpolatePoints instance to represent a detuning waveform.
            phase: a float number value to represent the phase.
            coords: an array-like containing (x, y) coordinates of the qubits.
            composed_wf: alternative approach to generate a sequence of waveforms
                instead of amplitude, detuning and phase
        """

        # perform some checks

        if composed_wf is not None:
            # implement it later as alternative to `InterpolatePoints`
            raise NotImplementedError("'composed_wf' argument is not available yet.")

        if not (
            isinstance(amplitude, InterpolatePoints)
            and isinstance(detuning, InterpolatePoints)
        ):
            raise TypeError(
                f"amplitude and detuning must be InterpolatePoints, not "
                f"{type(amplitude)} (amplitude), {type(detuning)} (detuning)."
            )

        if amplitude.duration != detuning.duration:
            raise ValueError(
                f"amplitude and detuning must have the same duration times;"
                f"amplitude duration: {amplitude.duration}, "
                f"detuning duration: {detuning.duration}."
            )

        num_qubits = len(coords)  # type: ignore [arg-type]
        phase_params = list(phase.parameters) if isinstance(phase, ParameterExpression) else []

        super().__init__(
            name="HG",
            num_qubits=num_qubits,
            params=list(set(amplitude.parameters + detuning.parameters + phase_params)),
            label="",
            unit="dt",
        )

        self.duration = amplitude.duration
        self._grid = grid_transform
        self._amplitude = amplitude
        self._detuning = detuning
        self._phase = phase

        new_coords = RegisterTransform(
            grid_transform=self._grid, coords=coords  # type: ignore [arg-type]
        ).coords if transform else coords

        self._analog_register = PasqalRegister.from_coordinates(
            coords=new_coords, prefix="q"  # type: ignore [arg-type]
        )

    @property
    def amplitude(self) -> InterpolatePoints:
        """Amplitude waveform-like data."""
        return self._amplitude

    @property
    def detuning(self) -> InterpolatePoints:
        """Detuning waveform-like data."""
        return self._detuning

    @property
    def phase(self) -> float:
        """Phase of the pulse as float."""
        return self._phase

    @property
    def coords(self) -> dict[str, AbstractArray]:
        """coordinates as a dictionary where the keys are the qubits ids and values
        are their (x, y) coordinates."""

        return self._analog_register.qubits

    @property
    def analog_register(self) -> PasqalRegister:
        """Analog register as a `PasqalRegister` instance. Not related to `qiskit`'s
        `QuantumRegister`."""

        return self._analog_register

    def power(self, exponent: float, annotated: bool = False):
        raise AttributeError("Cannot raise this gate to the power of `exponent`.")

    def control(
        self,
        num_ctrl_qubits: int = 1,
        label: str | None = None,
        ctrl_state: int | str | None = None,
        annotated: bool | None = None,
    ):
        raise AttributeError("Cannot have a control on an analog gate.")
