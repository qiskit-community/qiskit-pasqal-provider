"""PasqalCloud remote backend"""

from copy import deepcopy
from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import Options
from pasqal_cloud.job import CreateJob
from pulser_pasqal import PasqalCloud

from qiskit_pasqal_provider.providers.jobs import PasqalRemoteJob
from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.pulse_utils import (
    get_register_from_circuit,
    gen_seq,
)
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend,
    PasqalBackendType,
    PasqalJob,
)


class QPUBackend(PasqalBackend):
    """QPU backend"""

    _version: str = "0.1.0"
    _backend_name = PasqalBackendType.QPU
    _emulator = None

    def __init__(self, remote_config: RemoteConfig):
        """initialize and instantiate PasqalCloud."""

        super().__init__()

        self._cloud = PasqalCloud(
            username=remote_config.username,
            password=remote_config.password,
            project_id=remote_config.project_id,
            token_provider=remote_config.token_provider,
            endpoints=remote_config.endpoints,
            auth0=remote_config.auth0,
            webhook=remote_config.webhook,
        )

        self._executor = self._cloud._sdk_connection
        self._target = PasqalTarget(cloud=self._cloud)

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

        # define automatic layout based on register (limited functionality)
        new_register = analog_register.with_automatic_layout(device=self.target.device)

        # validate register from device layout; will throw an error if not compatible
        self.target.device.validate_register(new_register)

        # get a sequence
        seq = gen_seq(
            analog_register=new_register,
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
