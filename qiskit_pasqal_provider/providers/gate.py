"""Pasqal analog gate"""

from typing import Any, Union

import numpy as np
from numpy.typing import ArrayLike

from pulser.math import AbstractArray
from qiskit.circuit import Parameter, ParameterExpression
from qiskit.circuit.gate import Gate

from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister

CoordsKey = Union[str, int, float]


class InterpolatePoints:
    """
    A class to hold attributes for later use on `pulser`'s `InterpolateWaveform` class.
    It should be used to generate the points for the `HamiltonianGate` instance.
    """

    __slots__ = ("_values", "_duration", "_interpolator", "_interpolator_kwargs")

    def __init__(
        self,
        values: ArrayLike,
        duration: int | float | ParameterExpression = 1000,  # think how to define it
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
            interpolator: The SciPy interpolation class to use. Supports
                "PchipInterpolator" and "interp1d".
            **interpolator_kwargs: Extra parameters to give to the chosen
                interpolator class.
        """

        assert isinstance(duration, int | float | ParameterExpression)
        assert isinstance(interpolator, str)

        values = np.array(values)
        self._values = values
        self._duration = duration
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


class HamiltonianGate(Gate):
    """Hamiltonian gate, an analog gate."""

    def __init__(
        self,
        amplitude: InterpolatePoints,
        detuning: InterpolatePoints,
        phase: InterpolatePoints,
        coords: ArrayLike,
        composed_wf: Any | None = None,
    ):
        """
        Hamiltonian gate is an analog gate that provides the relevant functionalities
        to use analog quantum computing in a circuit-like environment.

        Args:
            amplitude: an InterpolatePoints instance to represent an amplitude waveform.
            detuning: an InterpolatePoints instance to represent a detuning waveform.
            phase: an InterpolatePoints instance to represent a phase waveform.
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
            and isinstance(phase, InterpolatePoints)
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

        super().__init__(
            name="HG",
            num_qubits=num_qubits,
            params=[],
            label="",
            duration=amplitude.duration,  # qiskit emits warning on this, but it's needed
            unit="dt",
        )

        self._amplitude = amplitude
        self._detuning = detuning
        self._phase = phase
        self._analog_register = PasqalRegister.from_coordinates(coords, prefix="q")

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
