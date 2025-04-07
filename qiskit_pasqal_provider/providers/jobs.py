"""This module implements the qiskit job class used for PasqalBackend objects."""

from typing import Any

from qiskit.providers.jobstatus import JobStatus, JOB_FINAL_STATES

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.providers.job_base import PasqalJob
from qiskit_pasqal_provider.providers.result import PasqalResult
from qiskit_pasqal_provider.utils import PasqalEmulator


class PasqalLocalJob(PasqalJob):
    """Class to encapsulate local jobs submitted to Pasqal backends."""

    _backend: PasqalBackend
    _result: PasqalResult | None
    _status: JobStatus
    _emulator: PasqalEmulator

    def __init__(self, backend: PasqalBackend, job_id: str, **kwargs: Any):
        """
        A Pasqal job for local emulators.

        Args:
            backend: Pasqal backends (must be an emulator)
            job_id: job id of the execution
            emulator: which emulator to use
            **kwargs:
        """

        super().__init__(job_id=job_id, **kwargs)
        self._backend = backend
        self._result = None
        self._status = JobStatus.INITIALIZING
        self._emulator = backend.emulator

    def backend(self) -> PasqalBackend:
        """Pasqal backend instance."""
        return self._backend

    def submit(self) -> None:
        """Submit the job to the backend for execution."""
        self._status = JobStatus.RUNNING
        results = self._emulator.run(progress_bar=True)
        self.metadata["success"] = True
        self._result = PasqalResult(
            backend_name=self.backend().name,
            job_id=self._job_id,
            results=results,
            metadata=self.metadata,
        )
        self._status = JobStatus.DONE

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

    def cancel(self) -> Any:
        """Attempt to cancel the job."""
        raise NotImplementedError()
