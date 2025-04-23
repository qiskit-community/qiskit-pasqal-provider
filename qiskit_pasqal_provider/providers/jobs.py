"""This module implements the qiskit job class used for PasqalBackend objects."""

from typing import Any

from qiskit.providers.jobstatus import JobStatus
from pulser.backend.remote import JobParams, RemoteResults

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.providers.job_base import PasqalJob
from qiskit_pasqal_provider.providers.result import PasqalResult
from qiskit_pasqal_provider.utils import PasqalExecutor


class PasqalLocalJob(PasqalJob):
    """Class to encapsulate local jobs submitted to Pasqal backends."""

    _backend: PasqalBackend
    _result: PasqalResult | None
    _status: JobStatus
    _executor: PasqalExecutor

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
        self._executor = backend.backend_executor

    def submit(self) -> None:
        """Submit the job to the backend for execution."""
        self._status = JobStatus.RUNNING
        results = self._executor.run(progress_bar=True)
        self.metadata["success"] = True
        self._result = PasqalResult(
            backend_name=self.backend().name,
            job_id=self._job_id,
            results=results,
            metadata=self.metadata,
        )
        self._status = JobStatus.DONE

    def cancel(self) -> Any:
        """Attempt to cancel the job."""
        raise NotImplementedError()


class PasqalRemoteJob(PasqalJob):
    """A Pasqal job for remote executors (emulator or QPU)."""

    _backend: PasqalBackend
    _result: PasqalResult | None
    _status: JobStatus
    _executor: PasqalExecutor

    def __init__(
        self,
        job_id: str,
        job_params: list[JobParams],
        wait: bool = False,
        **kwargs: Any
    ):
        """"""
        super().__init__(job_id=job_id, **kwargs)
        self._job_params = job_params
        self._wait = wait

    def submit(self) -> None:
        """"""
        self._status = JobStatus.RUNNING
        results = self._executor.run(job_params=self._job_params, wait=self._wait)

        if isinstance(results, RemoteResults):
            self.metadata["success"] = True
            self._result = PasqalResult(
                backend_name=self.backend().name,
                job_id=self._job_id,
                results=results,
                metadata=self.metadata,
            )
            self._status = JobStatus.DONE

    def cancel(self) -> Any:
        """Attempt to cancel the job."""
        raise NotImplementedError()
