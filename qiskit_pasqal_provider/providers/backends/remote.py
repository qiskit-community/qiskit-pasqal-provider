"""Remote base backend"""

from typing import Union, Any

from pulser import Register
from qiskit import QuantumCircuit
from qiskit.pulse import Schedule, ScheduleBlock

from qiskit_pasqal_provider.providers.backend_base import (
    PasqalBackend,
    PasqalBackendType,
)
from qiskit_pasqal_provider.providers.backends.emu_tn import EmuTnBackend
from qiskit_pasqal_provider.providers.backends.emu_free import EmuFreeBackend
from qiskit_pasqal_provider.providers.backends.qpu import QPUBackend
from qiskit_pasqal_provider.providers.jobs import PasqalJob
from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister


class PasqalRemoteBackend(PasqalBackend):
    """PasqalRemoteBackend."""

    def __new__(
        cls,
        backend: PasqalBackendType | str,
        remote_config: RemoteConfig,
        **_options: Any,
    ):
        # cloud = PasqalCloud
        match backend:
            case "remote-emu-free":
                return EmuFreeBackend(remote_config)

            case "remote-emu-tn":
                return EmuTnBackend(remote_config)

            case "qpu":
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
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | Register | None = None,
        **options: Any,
    ) -> PasqalJob:
        """

        Args:
            run_input (QuantumCircuit, Schedule, ScheduleBlock): the block of instructions
                to be run
            register (PasqalRegister): the register to be used in the instruction execution
            **options: additional configuration options for the run

        Returns:
            A PasqalJob instance.
        """
        raise NotImplementedError()
