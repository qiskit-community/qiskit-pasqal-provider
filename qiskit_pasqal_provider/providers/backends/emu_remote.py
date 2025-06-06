"""Remote emulator backend"""

from copy import deepcopy
from typing import Any

from pasqal_cloud import CreateJob, EmulatorType
from pulser.register import Register
from pulser_pasqal import PasqalCloud
from qiskit import QuantumCircuit
from qiskit.providers import Options

from qiskit_pasqal_provider.providers.abstract_base import PasqalBackend, PasqalJob
from qiskit_pasqal_provider.providers.jobs import PasqalRemoteJob
from qiskit_pasqal_provider.providers.pulse_utils import (
    PasqalRegister,
    gen_seq,
    get_register_from_circuit,
)
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.utils import RemoteConfig


class EmuRemoteBackend(PasqalBackend):
    """Remotely emulate backends. It gathers the remote backends."""

    def __init__(
        self,
        backend_name: str,
        emulator: EmulatorType,
        remote_config: RemoteConfig,
        target: PasqalTarget | None = None,
    ):
        """initialize and instantiate PasqalCloud."""

        super().__init__()

        self._backend_name = backend_name
        self._emulator = emulator
        self._cloud = PasqalCloud(
            username=remote_config.username,
            password=remote_config.password,
            project_id=remote_config.project_id,
        )

        self._executor = self._cloud._sdk_connection
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
        Runs a quantum circuit for a given remote emulated execution interface,
        namely `SamplerV2`.

        Args:
            run_input: the quantum circuit to be run.
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            wait: whether to wait for all the results to be retrieved. Default `True`.
            **options: extra options to pass to the backend if needed.

        Returns:
            A `PasqalJob` object containing the results from the execution interface.
        """

        assert shots is not None, "shots must not be None. Choose an integer value."

        analog_register: Register | PasqalRegister = get_register_from_circuit(
            run_input
        )

        if self._emulator == EmulatorType.EMU_FRESNEL:
            # define automatic layout based on register (limited functionality)
            analog_register = analog_register.with_automatic_layout(
                device=self.target.device
            )

            # validate register from device layout; will throw an error if not compatible
            self.target.device.validate_register(analog_register)

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
