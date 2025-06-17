"""Pasqal analog gate"""

from typing import Any, Union

from numpy.typing import ArrayLike
from pulser.math import AbstractArray
from qiskit.circuit import ParameterExpression
from qiskit.circuit.gate import Gate

from qiskit_pasqal_provider.providers.pulse_utils import (
    GridLiteralType,
    InterpolatePoints,
    PasqalRegister,
    RegisterTransform,
)

CoordsKey = Union[str, int, float]


class HamiltonianGate(Gate):
    """Hamiltonian gate, an analog gate."""

    def __init__(
        self,
        amplitude: InterpolatePoints,
        detuning: InterpolatePoints,
        phase: float | InterpolatePoints | ParameterExpression,
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
            grid_transform: a string of which grid transform to use. Default to "triangular".
            composed_wf: alternative approach to generate a sequence of waveforms
                instead of amplitude, detuning and phase. Default to None.
            transform: whether the coordinates need to be transformed into atoms coordinates.
                Default to False.
        """

        # perform some checks

        if composed_wf is not None:
            # implement it later as alternative to `InterpolatePoints`
            raise NotImplementedError("'composed_wf' argument is not available yet.")

        if not isinstance(amplitude, InterpolatePoints):
            raise TypeError(
                f"amplitude must be InterpolatePoints, not {type(amplitude)}."
            )

        if not isinstance(detuning, InterpolatePoints):
            raise TypeError(
                f"detuning must be InterpolatePoints, not {type(detuning)}."
            )

        if not isinstance(phase, InterpolatePoints | float | ParameterExpression):
            raise TypeError(
                f"phase must be either InterpolatePoints, float or ParameterExpression, not "
                f"{type(phase)}."
            )

        if amplitude.duration != detuning.duration:
            raise ValueError(
                f"amplitude and detuning must have the same duration times; "
                f"amplitude duration: {amplitude.duration}, "
                f"detuning duration: {detuning.duration}."
            )

        if len(amplitude) != len(detuning):
            raise ValueError(
                f"amplitude and detuning must have the same values' length; "
                f"amplitude length: {len(amplitude)}, "
                f"detuning length: {len(detuning)}."
            )

        num_qubits = len(coords)  # type: ignore [arg-type]
        phase_params = (
            list(phase.parameters) if isinstance(phase, ParameterExpression) else []
        )

        super().__init__(
            name="HG",
            num_qubits=num_qubits,
            params=list(set(amplitude.parameters + detuning.parameters + phase_params)),
            label="",
        )

        self.duration = amplitude.duration
        self._grid = grid_transform
        self._amplitude = amplitude
        self._detuning = detuning
        self._phase = phase

        new_coords = (
            RegisterTransform(
                grid_transform=self._grid, coords=coords  # type: ignore [arg-type]
            ).coords
            if transform
            else coords
        )

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
    def phase(self) -> float | InterpolatePoints | ParameterExpression:
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
