"""EMU-TN remote backend"""

from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import Options
from pulser_pasqal.backends import EmuTNBackend

from qiskit_pasqal_provider.providers.abstract_base import PasqalBackend, PasqalJob
from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.target import PasqalTarget

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
        run_input: QuantumCircuit,
        shots: int | None = None,
        values: dict | None = None,
        **options: Any,
    ) -> PasqalJob:
        pass
