"""Pasqal base backends"""

import sys
import logging
from abc import ABC, abstractmethod
from typing import Any, cast

from qiskit import QuantumCircuit
from qiskit.primitives import BasePrimitiveJob
from qiskit.providers import BackendV2, JobStatus
from qiskit.providers.jobstatus import JOB_FINAL_STATES
from pasqal_cloud import SDK as PasqalSDK, EmulatorType
from pulser.backend.remote import JobParams, RemoteResults
from pulser.register.register_layout import RegisterLayout
from pulser_simulation.simresults import SimulationResults

from .layouts import PasqalLayout
from .result import PasqalResult
from .target import PasqalTarget
from ..utils import PasqalExecutor


# check whether python version is equal or greater than 3.12 to decide which
#   StrEnum version to import from
if sys.version_info >= (3, 12):
    from enum import StrEnum
else:
    from qiskit_pasqal_provider.utils import StrEnum


logger = logging.getLogger(__name__)


class PasqalBackendType(StrEnum):
    """
    Pasqal backend StrEnum to choose between emulators/QPUs.

    Options:

    - QUTIP
    - EMU_MPS
    - REMOTE_EMU_FREE
    - REMOTE_EMU_MPS
    - REMOTE_EMU_FRESNEL
    - FRESNEL
    """

    QUTIP = "qutip"
    EMU_MPS = "emu-mps"
    REMOTE_EMU_FREE = "remote-emu-free"
    REMOTE_EMU_MPS = "remote-emu-mps"
    REMOTE_EMU_FRESNEL = "remote-emu-fresnel"
    FRESNEL = "fresnel"


class PasqalBackend(BackendV2, ABC):
    """PasqalBackend base class."""

    _target: PasqalTarget
    _layouts: PasqalLayout | RegisterLayout
    _backend_name: str | PasqalBackendType
    _version: str
    _executor: PasqalExecutor | PasqalSDK  # pylint: disable=E0601
    _emulator: EmulatorType | None

    @property
    def backend_name(self) -> str | PasqalBackendType:
        """Backend name"""
        return self._backend_name

    @property
    def executor(self) -> PasqalExecutor | PasqalSDK:
        """Pasqal emulator or QPU instance"""
        return self._executor

    @property
    def emulator(self) -> EmulatorType | None:
        """Emulator object"""
        return self._emulator

    @abstractmethod
    def run(
        self,
        run_input: QuantumCircuit,
        shots: int | None = None,
        values: dict | None = None,
        **options: Any,
    ) -> "PasqalJob":
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


class PasqalJob(BasePrimitiveJob[PasqalResult, JobStatus], ABC):
    """ABC for Pasqal Jobs"""

    _backend: PasqalBackend
    _result: PasqalResult | None
    _status: JobStatus
    _executor: PasqalExecutor | PasqalSDK

    def backend(self) -> PasqalBackend:
        """Pasqal backend instance."""
        return self._backend

    def result(self) -> PasqalResult:
        """Return the result of the job."""
        return self._result

    def status(self) -> JobStatus:
        """Return the status of the job."""
        return self._status

    def done(self) -> bool:
        """Return whether the job was successfully run."""
        return self._status == JobStatus.DONE

    def running(self) -> bool:
        """Return whether the job is actively running."""
        return self._status == JobStatus.RUNNING

    def cancelled(self) -> bool:
        """Return whether the job has been cancelled."""
        return self._status == JobStatus.CANCELLED

    def in_final_state(self) -> bool:
        """Return whether the job is in a final job state such as `DONE` or `ERROR`."""
        return self._status in JOB_FINAL_STATES

    def _eval_run_method(
        self,
        job_params: list[JobParams] | None = None,
        wait: bool | None = None,
    ) -> SimulationResults | RemoteResults:
        """
        Check the self._executor run method signature;
        Only compatible with local run.
        """

        import inspect  # pylint: disable=import-outside-toplevel

        self._executor = cast(PasqalExecutor, self._executor)
        run_arg_spec = inspect.getfullargspec(self._executor.run)

        # default case (works with QPU and default remote backends): ['job_params', 'wait']
        if set(run_arg_spec.args) == {"job_params", "wait"}:
            return self._executor.run(job_params=job_params, wait=wait)

        # case where there are parameters but can be ignored
        if (
            # excluding 'self'
            (len(run_arg_spec.args) - 1) > 0
            and (run_arg_spec.defaults is None or len(run_arg_spec.defaults) > 0)
        ):
            return self._executor.run()

        # no args case
        if len(run_arg_spec.args) == 0 or (
            "self" in run_arg_spec.args and len(run_arg_spec.args) == 1
        ):
            return self._executor.run()

        # other cases, implementation needed
        raise NotImplementedError()
