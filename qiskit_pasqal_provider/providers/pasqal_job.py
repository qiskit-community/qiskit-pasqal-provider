"""This module implements the qiskit job class used for PasqalBackend objects."""

from abc import ABC
from typing import Union

from pulser.result import Result
from pulser_simulation import QutipEmulator
from pulser_simulation.simresults import SimulationResults
from qiskit.providers import JobStatus
from qiskit.providers import JobV1 as Job
from qiskit.providers.backend import Backend
from qiskit.result import Result
from qiskit.result.models import ExperimentResult, ExperimentResultData


class PasqalJob(Job, ABC):
    pass


class PasqalResults(Result):
    def __init__(
        self,
        qobj_id,
        job_id,
        success,
        results: Union[Result, SimulationResults],
        date=None,
        status=None,
        header=None,
        **kwargs,
    ):
        if isinstance(results, SimulationResults):
            _data = ExperimentResultData(counts=results.sample_final_state())
        else:
            raise NotImplementedError
        _results: list[ExperimentResult] = [
            ExperimentResult(shots=1000, success=True, data=_data)
        ]
        super().__init__(
            "pasqal_local_backend",
            "0.0.1",
            qobj_id,
            job_id,
            success,
            _results,
            date,
            status,
            header,
            **kwargs,
        )


class PasqalLocalJob(PasqalJob):
    def __init__(
        self, backend: Backend | None, job_id: str, emulator: QutipEmulator, **kwargs
    ) -> None:
        super().__init__(backend, job_id, **kwargs)
        self._result: Result = None
        self._status = JobStatus.INITIALIZING
        self._emulator = emulator

    def submit(self) -> None:
        self._status = JobStatus.RUNNING
        results = self._emulator.run(progress_bar=True)
        self._result = PasqalResults(self.job_id, self.job_id, True, results=results)
        self._status = JobStatus.DONE

    def result(self) -> Result:
        return self._result

    def status(self) -> JobStatus:
        return self._status
