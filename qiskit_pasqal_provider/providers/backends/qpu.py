"""Pasqal Cloud QPU backend"""

from copy import deepcopy
from typing import Any

from pasqal_cloud import PasqalCloudConnection
from pasqal_cloud.job import CreateJob
from qiskit import QuantumCircuit
from qiskit.providers import Options

from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend,
    PasqalBackendType,
    PasqalJob,
)
from qiskit_pasqal_provider.providers.jobs import PasqalRemoteJob
from qiskit_pasqal_provider.providers.pulse_utils import (
    gen_seq,
    get_register_from_circuit,
    place_register,
)
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.utils import RemoteConfig


class QPUBackend(PasqalBackend):
    """QPU backend"""

    _version: str = "0.1.0"
    _backend_name = PasqalBackendType.FRESNEL

    def __init__(self, remote_config: RemoteConfig, target: PasqalTarget | None = None):
        """initialize and instantiate PasqalCloudConnection."""

        super().__init__()

        self._cloud = PasqalCloudConnection(
            username=remote_config.username,
            password=remote_config.password,
            project_id=remote_config.project_id,
            token_provider=remote_config.token_provider,
            endpoints=remote_config.endpoints,
            auth0=remote_config.auth0,
            webhook=remote_config.webhook,
        )

        self._executor = self._cloud.cloud_client
        self._target = target if target is not None else PasqalTarget(cloud=self._cloud)

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
        Run a quantum circuit for a given execution interface, namely `SampleV2`.

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

        if shots is None:
            raise ValueError("shots must not be None. Choose an integer value.")

        analog_register = place_register(
            get_register_from_circuit(run_input),
            self.target.device,
            self.target.layout,
        )

        # get a sequence
        seq = gen_seq(
            analog_register=analog_register,
            device=self.target.device,
            circuit=run_input,
        )

        if values:
            seq = seq.build(**values)

        job_params = [CreateJob(runs=shots, variables=values)]

        backend = deepcopy(self)

        job = PasqalRemoteJob(backend, seq=seq, job_params=job_params, wait=wait)

        job.submit()
        return job
