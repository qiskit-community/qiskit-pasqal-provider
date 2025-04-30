"""QuTiP backend"""

import copy
import uuid
from typing import Any

from pulser_simulation import QutipEmulator
from qiskit import QuantumCircuit
from qiskit.providers import Options

from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend, PasqalBackendType,
    PasqalJob
)
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.jobs import PasqalLocalJob
from qiskit_pasqal_provider.providers.pulse_utils import (
    get_register_from_circuit,
    gen_seq,
)


class QutipEmulatorBackend(PasqalBackend):
    """QutipEmulatorBackend to emulate pulse sequences using QuTiP."""

    _version: str = "0.1.0"
    backend_name = PasqalBackendType.QUTIP

    def __init__(self, target: PasqalTarget, **options: Any):
        """

        Args:
            target (PasqalTarget): The target of the pulse sequence.
            **options: additional configuration options
        """

        backend_name = self.__class__.__name__
        super().__init__(name=backend_name, **options)
        self._target = target
        self._layout = self.target.layout

    @property
    def target(self) -> PasqalTarget:
        return self._target

    @property
    def max_circuits(self) -> None:
        return None

    @classmethod
    def _default_options(cls) -> Options:
        return Options()

    def run(
        self,
        run_input: QuantumCircuit,
        shots: int | None = None,
        values: dict | None = None,
        **options: Any,
    ) -> PasqalJob:
        """
        Run a quantum circuit for a given execution interface, namely `Sampler`.

        Args:
            run_input: the quantum circuit to be run.
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            **options: extra options to pass to the backend if needed.

        Returns:
            A PasqalJob instance containing the results from the execution interface.
        """

        if not isinstance(run_input, QuantumCircuit):
            raise ValueError("'run_input' argument must be a QuantumCircuit")

        # get the register from the analog gate inside `run_input` argument (QuantumCircuit)
        analog_register = get_register_from_circuit(run_input)

        # Run a program on Pasqal backend
        seq = gen_seq(
            analog_register=analog_register,
            device=self.target.device,
            circuit=run_input,
        )

        # building into a regular sequence by defining attribute values for all declared variables
        if values:
            seq.build(**values)

        # initialise the backend from sequence.
        # In the sequence the register and device is encoded
        # we can imagine moving that to the Qiskit Backend
        self._executor = QutipEmulator.from_sequence(seq)
        backend = copy.deepcopy(self)
        job_id = str(uuid.uuid4())

        job = PasqalLocalJob(
            backend=backend,
            job_id=job_id,
            shots=shots,
            qojb_id=job_id,
            backend_version=self._version,
        )
        job.submit()
        return job
