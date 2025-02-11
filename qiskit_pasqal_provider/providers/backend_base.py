"""Pasqal base backends"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Union

from qiskit import QuantumCircuit
from qiskit.providers import BackendV2
from qiskit.pulse import Schedule, ScheduleBlock
from pulser.register.register_layout import RegisterLayout

from .layouts import PasqalLayout
from .pasqal_devices import PasqalTarget
from .jobs import PasqalJob
from .pulse_utils import PasqalRegister

try:
    from enum import StrEnum
except ImportError:
    from qiskit_pasqal_provider.utils import StrEnum  # type: ignore [assignment]


logger = logging.getLogger(__name__)


class PasqalBackendType(StrEnum):
    """Pasqal backend StrEnum to choose between emulators/QPUs"""

    QUTIP = "qutip"
    EMU_MPS = "emu-mps"
    REMOTE_EMU_FREE = "remote-emu-free"
    REMOTE_EMU_TN = "remote-emu-tn"
    QPU = "qpu"


class PasqalBackend(BackendV2, ABC):
    """PasqaqlBackend base class."""

    _target: PasqalTarget
    _layouts: PasqalLayout | RegisterLayout

    @abstractmethod
    def run(
        self,
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | None = None,
        **options: Any,
    ) -> PasqalJob:
        pass
