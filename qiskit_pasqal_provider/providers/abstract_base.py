"""Pasqal base backends"""

import sys
import logging
from abc import ABC, abstractmethod
from typing import Any

from pulser.backend.remote import JobParams, RemoteResults
from pulser_simulation.simresults import SimulationResults

from qiskit import QuantumCircuit
from qiskit.primitives import BasePrimitiveJob
from qiskit.providers import BackendV2, JobStatus
from pulser.register.register_layout import RegisterLayout
from qiskit.providers.jobstatus import JOB_FINAL_STATES

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
    - REMOTE_EMU_TN
    - QPU

    """

    QUTIP = "qutip"
    EMU_MPS = "emu-mps"
    REMOTE_EMU_FREE = "remote-emu-free"
    REMOTE_EMU_TN = "remote-emu-tn"
    QPU = "qpu"


class PasqalBackend(BackendV2, ABC):
    """PasqalBackend base class."""

    _target: PasqalTarget
    _layouts: PasqalLayout | RegisterLayout
    _backend_name: str | PasqalBackendType
    _version: str
    _executor: PasqalExecutor  # pylint: disable=E0601

    @property
    def backend_executor(self) -> PasqalExecutor:
        """Pasqal emulator or QPU instance"""
        return self._executor

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
    _executor: PasqalExecutor

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
        """Check the self._executor run method signature"""

        import inspect

        run_arg_spec = inspect.getfullargspec(self._executor.run)

        # default case (works with QPU and default remote backends): ['job_params', 'wait']
        if set(run_arg_spec.args) == {'job_params', 'wait'}:
            return self._executor.run(job_params=job_params, wait=wait)

        # case where there are parameters but can be ignored
        if (
            # excluding 'self'
            (len(run_arg_spec.args) - 1) > 0
            and (run_arg_spec.defaults is None or len(run_arg_spec.defaults) > 0)
        ):
                return self._executor.run()

        # no args case
        else:
            return self._executor.run()

        # other cases, implementation needed
        raise NotImplementedError()
