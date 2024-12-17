"""This module implements the qiskit job class used for PasqalBackend objects."""

from abc import ABC
from typing import Union

from pulser.result import Result as PulserResult
from pulser_simulation import QutipEmulator
from pulser_simulation.simresults import SimulationResults
from qiskit.providers import JobStatus
from qiskit.providers import JobV1 as Job
from qiskit.providers.backend import Backend
from qiskit.result import Result as QiskitResult
from qiskit.result.models import ExperimentResult, ExperimentResultData


class PasqalJob(Job, ABC):
    """ABC for Pasqal Jobs"""


class PasqalResult(QiskitResult):
    """To hold and convert Pasqal results to Qiskit Results"""

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        qobj_id,
        job_id,
        success,
        results: Union[PulserResult, SimulationResults],
        date=None,
        status=None,
        header=None,
        **kwargs,
    ) -> None:
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
    """Class to encapsulate local jobs submitted to Pasqal backends"""

    def __init__(
        self, backend: Backend | None, job_id: str, emulator: QutipEmulator, **kwargs
    ) -> None:
        super().__init__(backend, job_id, **kwargs)
        self._result: PasqalResult = None
        self._status = JobStatus.INITIALIZING
        self._emulator = emulator

    def submit(self) -> None:
        self._status = JobStatus.RUNNING
        results = self._emulator.run(progress_bar=True)
        self._result = PasqalResult(self.job_id, self.job_id, True, results=results)
        self._status = JobStatus.DONE

    def result(self) -> PasqalResult:
        return self._result

    def status(self) -> JobStatus:
        return self._status
