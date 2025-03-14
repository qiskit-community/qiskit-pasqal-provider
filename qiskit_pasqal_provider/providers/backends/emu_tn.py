"""EMU-TN remote backend"""

from typing import Any, Union

from qiskit import QuantumCircuit
from qiskit.pulse import Schedule, ScheduleBlock
from qiskit.providers import Options

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister
from qiskit_pasqal_provider.providers.jobs import PasqalJob

try:
    from pulser_pasqal import PasqalCloud
except ImportError as exc:
    raise ImportError(
        "'pulser-pasqal' package not found. Please install it through 'pip install pulser-pasqal'."
    ) from exc


class EmuTnBackend(PasqalBackend):
    """EMU-TN remote backend"""

    def __init__(self, remote_config: RemoteConfig):
        """initialize and instantiate PasqalCloud."""
        super().__init__()
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
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
        **options: Any,
    ) -> PasqalJob:
        pass
