"""Pasqal base backends"""

import sys
import logging
from abc import ABC, abstractmethod
from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import BackendV2
from pulser.register.register_layout import RegisterLayout

from .layouts import PasqalLayout
from .target import PasqalTarget
from .job_base import PasqalJob
from ..utils import PasqalEmulator


# check whether python version is equal or greater than 3.12 to decide which
#   StrEnum version to import from
if sys.version_info >= (3, 12):
    from enum import StrEnum
else:
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
    _version: str
    _emulator: PasqalEmulator  # pylint: disable=E0601

    @property
    def emulator(self) -> PasqalEmulator:
        """Pasqal emulator instance"""
        return self._emulator

    @abstractmethod
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
