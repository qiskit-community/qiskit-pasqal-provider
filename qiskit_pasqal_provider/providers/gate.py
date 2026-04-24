"""Pasqal analog gate"""

from typing import Any, Union

from numpy.typing import ArrayLike
from pulser.math import AbstractArray
from qiskit.circuit import QuantumCircuit
from qiskit.circuit import ParameterExpression
from qiskit.circuit.gate import Gate

from qiskit_pasqal_provider.providers.pulse_utils import (
    GridLiteralType,
    InterpolatePoints,
    PasqalRegister,
    RegisterTransform,
)

CoordsKey = Union[str, int, float]
GridCodeType = float
_QASM3_TRANSPORT_SCHEMA_VERSION = 1.0
_GRID_TO_CODE: dict[GridLiteralType, GridCodeType] = {
    "linear": 0.0,
    "triangular": 1.0,
    "square": 2.0,
}
_CODE_TO_GRID: dict[GridCodeType, GridLiteralType] = {
    code: grid for grid, code in _GRID_TO_CODE.items()
}


def _qasm3():
    try:
        from qiskit import qasm3
    except ImportError as exc:
        raise ImportError(
            "OpenQASM3 transport requires the 'qasm3' extra. Install "
            "qiskit-pasqal-provider[qasm3] or qiskit-pasqal-provider[all]."
        ) from exc
    return qasm3


def _to_float(value: Any, label: str) -> float:
    if isinstance(value, ParameterExpression):
        if value.parameters:
            raise ValueError(
                f"{label} must be numeric for OpenQASM3 transport serialization."
            )
        value = value.numeric()

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc


def _to_float_list(values: Any, label: str) -> list[float]:
    if isinstance(values, ParameterExpression):
        raise ValueError(
            f"{label} must be numeric for OpenQASM3 transport serialization."
        )

    if isinstance(values, str):
        raise ValueError(f"{label} must be an array-like sequence.")

    try:
        items = list(values)
    except TypeError as exc:
        raise ValueError(f"{label} must be an array-like sequence.") from exc

    return [_to_float(value, f"{label}[{idx}]") for idx, value in enumerate(items)]


def _encode_interpolate_points(
    points: InterpolatePoints, label: str
) -> tuple[list[float], list[float], float]:
    values = _to_float_list(points.values, f"{label}.values")
    times = (
        [] if points.times is None else _to_float_list(points.times, f"{label}.times")
    )
    if times and len(values) != len(times):
        raise ValueError(f"{label}.times must have the same length as {label}.values.")
    duration = _to_float(points.duration, f"{label}.duration")
    return values, times, duration


def _take_slice(
    params: list[float], idx: int, size: int, label: str
) -> tuple[list[float], int]:
    end = idx + size
    if end > len(params):
        raise ValueError(
            f"OpenQASM3 transport payload is truncated while reading {label}."
        )
    return params[idx:end], end


def _insert_gate_declaration(
    program: str, gate_name: str, num_params: int, num_qubits: int
) -> str:
    lines = program.splitlines()
    declaration_params = ", ".join(f"p{k}" for k in range(num_params))
    declaration_qubits = ", ".join(f"q{k}" for k in range(num_qubits))
    declaration = f"gate {gate_name}({declaration_params}) {declaration_qubits} {{}}"
    insert_idx = next(
        (idx for idx, line in enumerate(lines) if line.startswith("qubit[")), len(lines)
    )
    lines.insert(insert_idx, declaration)
    return "\n".join(lines) + "\n"


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
            phase: a float, InterpolatePoints or qiskit ParameterExpression value.
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
                f"The amplitude parameter must be `InterpolatePoints` type, not {type(amplitude)}."
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
            sorted(phase.parameters, key=lambda param: param.name)
            if isinstance(phase, ParameterExpression)
            else []
        )

        super().__init__(
            name="HG",
            num_qubits=num_qubits,
            params=list(
                dict.fromkeys(amplitude.parameters + detuning.parameters + phase_params)
            ),
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
            coords=new_coords, prefix="q"
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

    def to_openqasm3_transport_params(self) -> list[float]:
        """Encode this gate as a numeric payload for an OpenQASM3-compatible transport format."""

        amp_values, amp_times, amp_duration = _encode_interpolate_points(
            self.amplitude, "amplitude"
        )
        det_values, det_times, det_duration = _encode_interpolate_points(
            self.detuning, "detuning"
        )
        if abs(amp_duration - det_duration) > 1e-12:
            raise ValueError(
                "Amplitude and detuning duration must match for OpenQASM3 transport."
            )

        phase_mode = 0.0
        phase_scalar = 0.0
        phase_values: list[float] = []
        phase_times: list[float] = []
        if isinstance(self.phase, InterpolatePoints):
            phase_mode = 1.0
            phase_values, phase_times, _ = _encode_interpolate_points(
                self.phase, "phase"
            )
        else:
            phase_scalar = _to_float(self.phase, "phase")

        # Header layout (12 scalars):
        # [schema, num_qubits, grid_code, phase_mode, phase_scalar, duration,
        #  amp_size, det_size, phase_size, amp_times_size, det_times_size,
        #  phase_times_size]
        payload = [
            _QASM3_TRANSPORT_SCHEMA_VERSION,
            float(self.num_qubits),
            _GRID_TO_CODE[self._grid],
            phase_mode,
            phase_scalar,
            amp_duration,
            float(len(amp_values)),
            float(len(det_values)),
            float(len(phase_values)),
            float(len(amp_times)),
            float(len(det_times)),
            float(len(phase_times)),
        ]

        for idx, coord in enumerate(self.analog_register.qubits.values()):
            payload.extend(
                [
                    _to_float(coord[0], f"coords[{idx}].x"),
                    _to_float(coord[1], f"coords[{idx}].y"),
                ]
            )

        # Variable-size sections in order:
        # coords_flat(2*num_qubits), amp_values, amp_times,
        # det_values, det_times, phase_values, phase_times.
        payload.extend(amp_values)
        payload.extend(amp_times)
        payload.extend(det_values)
        payload.extend(det_times)
        payload.extend(phase_values)
        payload.extend(phase_times)
        return payload

    @classmethod
    def from_openqasm3_transport_params(cls, params: list[float]) -> "HamiltonianGate":
        """Build a HamiltonianGate from an OpenQASM3 transport payload."""
        # pylint: disable=too-many-locals,too-many-statements

        numeric_params = [_to_float(value, "transport parameter") for value in params]
        if len(numeric_params) < 12:
            raise ValueError("OpenQASM3 transport payload is too short.")

        # Decode fields from the 12-value header in the same order as encoding.
        idx = 0
        schema = int(round(numeric_params[idx]))
        idx += 1
        if schema != int(_QASM3_TRANSPORT_SCHEMA_VERSION):
            raise ValueError(
                f"Unsupported OpenQASM3 transport schema version: {schema}."
            )

        num_qubits = int(round(numeric_params[idx]))
        idx += 1

        grid_code = numeric_params[idx]
        idx += 1
        if grid_code not in _CODE_TO_GRID:
            raise ValueError(f"Unknown grid code in OpenQASM3 payload: {grid_code}.")
        grid = _CODE_TO_GRID[grid_code]

        phase_mode = int(round(numeric_params[idx]))
        idx += 1
        phase_scalar = numeric_params[idx]
        idx += 1

        duration = numeric_params[idx]
        idx += 1
        amp_size = int(round(numeric_params[idx]))
        idx += 1
        det_size = int(round(numeric_params[idx]))
        idx += 1
        phase_size = int(round(numeric_params[idx]))
        idx += 1
        amp_times_size = int(round(numeric_params[idx]))
        idx += 1
        det_times_size = int(round(numeric_params[idx]))
        idx += 1
        phase_times_size = int(round(numeric_params[idx]))
        idx += 1

        if amp_size < 1 or det_size < 1:
            raise ValueError(
                "OpenQASM3 transport payload requires non-empty waveforms."
            )

        # Decode variable-size sections in the same fixed order used at encode time.
        coords_flat, idx = _take_slice(
            numeric_params, idx, 2 * num_qubits, "coordinates"
        )
        coords = [
            [coords_flat[2 * atom_idx], coords_flat[2 * atom_idx + 1]]
            for atom_idx in range(num_qubits)
        ]

        amp_values, idx = _take_slice(numeric_params, idx, amp_size, "amplitude values")
        amp_times, idx = _take_slice(
            numeric_params, idx, amp_times_size, "amplitude times"
        )
        det_values, idx = _take_slice(numeric_params, idx, det_size, "detuning values")
        det_times, idx = _take_slice(
            numeric_params, idx, det_times_size, "detuning times"
        )
        phase_values, idx = _take_slice(numeric_params, idx, phase_size, "phase values")
        phase_times, idx = _take_slice(
            numeric_params, idx, phase_times_size, "phase times"
        )

        if idx != len(numeric_params):
            raise ValueError("OpenQASM3 transport payload has extra trailing values.")

        amplitude = InterpolatePoints(
            values=amp_values,
            duration=duration,
            times=amp_times or None,
        )
        detuning = InterpolatePoints(
            values=det_values,
            duration=duration,
            times=det_times or None,
        )

        if phase_mode == 0:
            phase: float | InterpolatePoints = phase_scalar
        elif phase_mode == 1:
            phase = InterpolatePoints(
                values=phase_values,
                duration=duration,
                times=phase_times or None,
            )
        else:
            raise ValueError(
                f"Unsupported phase mode in OpenQASM3 payload: {phase_mode}."
            )

        return cls(
            amplitude=amplitude,
            detuning=detuning,
            phase=phase,
            coords=coords,
            grid_transform=grid,
        )


def dumps_qpp_openqasm3(circuit: QuantumCircuit, gate_name: str = "HG") -> str:
    """Serialize a one-gate Hamiltonian circuit to an OpenQASM3 transport format."""
    # Example of generated OpenQASM3 for this transport format (shape only):
    # OPENQASM 3.0;
    # include "stdgates.inc";
    # gate HG(p0, p1, ..., pN) q0, q1, ..., qM {}
    # qubit[M+1] q;
    # HG(<transport-payload...>) q[0], q[1], ..., q[M];

    if len(circuit.data) != 1:
        raise ValueError("OpenQASM3 transport expects a circuit with exactly one gate.")

    operation = circuit.data[0].operation
    if not isinstance(operation, HamiltonianGate):
        raise ValueError(
            "OpenQASM3 transport expects a circuit with one HamiltonianGate."
        )

    payload = operation.to_openqasm3_transport_params()
    transport_circuit = QuantumCircuit(operation.num_qubits)
    transport_circuit.append(
        Gate(gate_name, operation.num_qubits, payload), transport_circuit.qubits
    )
    program = _qasm3().dumps(transport_circuit, basis_gates=("U", gate_name))
    return _insert_gate_declaration(
        program,
        gate_name=gate_name,
        num_params=len(payload),
        num_qubits=operation.num_qubits,
    )


def loads_qpp_openqasm3(program: str, gate_name: str = "HG") -> QuantumCircuit:
    """Deserialize an OpenQASM3 transport program into a Hamiltonian circuit."""

    transport_circuit = _qasm3().loads(program)
    if len(transport_circuit.data) != 1:
        raise ValueError("OpenQASM3 transport expects exactly one gate call.")

    operation = transport_circuit.data[0].operation
    if operation.name != gate_name:
        raise ValueError(
            f"OpenQASM3 transport expected gate '{gate_name}', found '{operation.name}'."
        )

    gate = HamiltonianGate.from_openqasm3_transport_params(
        [_to_float(value, "transport parameter") for value in operation.params]
    )
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, circuit.qubits)
    return circuit
