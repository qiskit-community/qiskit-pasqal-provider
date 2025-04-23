"""Base file for Pasqal job class (to avoid circular import)"""

from typing import Any
from abc import ABC

from qiskit.primitives import BasePrimitiveJob
from qiskit.providers.jobstatus import JobStatus, JOB_FINAL_STATES

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.providers.result import PasqalResult


class PasqalJob(BasePrimitiveJob[PasqalResult, JobStatus], ABC):
    """ABC for Pasqal Jobs"""

    _backend: PasqalBackend
    _result: PasqalResult | None
    _status: JobStatus

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
