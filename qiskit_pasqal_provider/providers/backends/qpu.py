"""PasqalCloud remote backend"""
import uuid
from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import Options
from pulser import QPUBackend as PasqalQPUBackend
from pulser.backend.remote import JobParams
from pulser_pasqal import PasqalCloud

from qiskit_pasqal_provider.providers.jobs import PasqalRemoteJob
from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.pulse_utils import (
    get_register_from_circuit,
    gen_seq,
)
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend, PasqalBackendType,
    PasqalJob
)


class QPUBackend(PasqalBackend):
    """QPU backend"""

    _version: str = "0.1.0"
    backend_name = PasqalBackendType.QPU

    def __init__(self, remote_config: RemoteConfig):
        """initialize and instantiate PasqalCloud."""
        super().__init__()
        # check whether pulser's `AnalogDevice` is compatible with QPU
        self._target = PasqalTarget(device="pasqal_device")
        self._cloud = PasqalCloud(**remote_config)

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
        wait: bool = True,
        **options: Any,
    ) -> PasqalJob:
        """
        Run a quantum circuit for a given execution interface, namely `Sampler`.

        Args:
            run_input: the quantum circuit to be run.
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            wait: Whether to wait until the results of the jobs become
                available.  If set to False, the call is non-blocking and the
                obtained results' status can be checked using their `status`
                property. Default to True.
            **options: extra options to pass to the backend if needed.

        Returns:
            A PasqalJob instance containing the results from the execution interface.
        """

        analog_register = get_register_from_circuit(run_input)

        # get a sequence
        seq = gen_seq(
            analog_register=analog_register,
            device=self.target.device,
            circuit=run_input,
        )

        if values:
            seq.build(**values)

        self._executor = PasqalQPUBackend(sequence=seq, connection=self._cloud)
        job_id = str(uuid.uuid4())
        job_params = [JobParams(runs=shots, variables=values)]

        job = PasqalRemoteJob(job_id=job_id, job_params=job_params, wait=wait, **options)
        job.submit()
        return job
