"""Remote base backend"""

from typing import Any

from qiskit import QuantumCircuit
from pasqal_cloud.device import EmulatorType

from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend,
    PasqalBackendType,
    PasqalJob,
)
from qiskit_pasqal_provider.providers.backends.emu_remote import EmuRemoteBackend
from qiskit_pasqal_provider.providers.backends.qpu import QPUBackend
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.utils import RemoteConfig


class PasqalRemoteBackend(PasqalBackend):
    """PasqalRemoteBackend."""

    def __new__(
        cls,
        backend: PasqalBackendType | str,
        remote_config: RemoteConfig,
        target: PasqalTarget | None = None,
        **_options: Any,
    ):
        # cloud = PasqalCloud
        match backend:
            case "remote-emu-free":
                return EmuRemoteBackend(
                    backend, EmulatorType.EMU_FREE, remote_config, target
                )

            case "remote-emu-mps":
                return EmuRemoteBackend(
                    backend, EmulatorType.EMU_MPS, remote_config, target
                )

            case "remote-emu-fresnel":
                return EmuRemoteBackend(
                    backend, EmulatorType.EMU_FRESNEL, remote_config, target
                )

            case "fresnel":
                return QPUBackend(remote_config)

            case _:
                raise NotImplementedError()

    @property
    def target(self):
        raise NotImplementedError()

    @property
    def max_circuits(self):
        raise NotImplementedError()

    @classmethod
    def _default_options(cls):
        raise NotImplementedError()

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
            run_input (QuantumCircuit): the quantum circuit to be run
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            **options: additional configuration options for the run

        Returns:
            A PasqalJob instance.
        """
        raise NotImplementedError()
