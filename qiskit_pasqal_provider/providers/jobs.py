"""This module implements the qiskit job class used for PasqalBackend objects."""

from typing import Any, cast

from qiskit.providers.jobstatus import JobStatus
from pasqal_cloud import SDK as PasqalSDK, Batch as PasqalBatch
from pasqal_cloud.job import CreateJob
from pulser.backend.remote import JobParams, Sequence

from qiskit_pasqal_provider.providers.abstract_base import PasqalBackend, PasqalJob
from qiskit_pasqal_provider.providers.result import PasqalResult
from qiskit_pasqal_provider.utils import PasqalExecutor


JOB_EXECUTION_FINISHED = {"DONE", "CANCELED", "TIMED_OUT", "ERROR"}


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
            **kwargs: extra arguments if needed
        """

        super().__init__(job_id=job_id, **kwargs)
        self._backend = backend
        self._result = None
        self._status = JobStatus.INITIALIZING
        self._executor = cast(PasqalExecutor, backend.executor)

    def submit(self) -> None:
        """Submit the job to the local backend for execution."""

        self._status = JobStatus.RUNNING
        results = self._eval_run_method()

        self.metadata["success"] = True
        self.metadata["config"] = getattr(self._executor, "_config", None)

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
    _executor: PasqalSDK
    _batch: PasqalBatch | None

    def __init__(
        self,
        backend: PasqalBackend,
        seq: Sequence,
        job_params: list[JobParams] | list[CreateJob],
        wait: bool = False,
        **kwargs: Any,
    ):
        """
        A Pasqal job for remote executors (emulator or QPU).

        Args:
            job_id: job id of the execution
            job_params: list of parameters for each job to execute
            wait: whether to wait until the results of the jobs become
                available. If set to False, the call is non-blocking and the
                obtained results' status can be checked using their `status`
                property.
            **kwargs: extra arguments if needed
        """

        super().__init__(job_id="", **kwargs)
        self._seq = seq
        self._backend = backend
        self._executor = cast(PasqalSDK, backend.executor)
        self._job_params = job_params
        self._wait = wait
        self._batch = None

    def submit(self) -> None:
        """To submit a job to a remote backend."""

        self._status = JobStatus.RUNNING

        if self._backend.backend_name == "QPU":
            self._batch = self._executor.create_batch(
                self._seq.to_abstract_repr(), self._job_params, wait=self._wait
            )

        else:
            self._batch = self._executor.create_batch(
                self._seq.to_abstract_repr(),
                self._job_params,
                emulator=self._backend.emulator,
                wait=self._wait,
            )

        self.metadata = {"batch": self._batch, "status": None}

        self._result = PasqalResult(
            backend_name=self.backend().name,
            job_id="",
            results=None,
            metadata=self.metadata,
        )

        match self.metadata["status"]:

            case "DONE":
                self._status = JobStatus.DONE

            case "TIMED_OUT" | "ERROR":
                self._status = JobStatus.ERROR

            case "CANCELED":
                self._status = JobStatus.CANCELLED

            case _:
                self._status = JobStatus.ERROR

    def cancel(self) -> Any:
        """Attempt to cancel the job."""

        self._batch.cancel()
