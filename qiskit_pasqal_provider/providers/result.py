"""Pasqal's result class tools"""

import copy
import json
import time
from collections import Counter
from collections.abc import Mapping
from typing import Any

from pasqal_cloud.batch import Batch as PasqalBatchData
from pasqal_cloud.job import Job as PasqalJobData
from pulser.backend import Results
from pulser.backend.remote import BatchStatus, RemoteResults
from pulser_simulation.simresults import SimulationResults
from qiskit.primitives import DataBin, PrimitiveResult, SamplerPubResult
from qiskit.result.models import ExperimentResult


class PasqalResult(PrimitiveResult[list[ExperimentResult]]):
    """To hold and convert Pasqal results to Qiskit Results."""

    def __init__(
        self,
        backend_name: str,
        job_id: str | list[str],
        results: SimulationResults | RemoteResults | dict | list | tuple | None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Constructor for results from Pasqal emulators and QPUs.

        Args:
            backend_name: Backend name as in `providers.abstract_base.PasqalBackendType` enum class
            job_id: The identifiable str value for the job.
            results: Pulser results from emulator or QPU
            metadata: Metadata that is common to all the results, such as `backend_version`,
                `shots`, `qobj_id`, `job_id`, `success`
        """

        _data: DataBin

        match results:

            case SimulationResults() | Results():
                _data = self._fetch_local_sim_results(results, metadata)

            case RemoteResults():

                if backend_name == "qpu":
                    _data = self._fetch_qpu_results(results, metadata)

                else:
                    # this branch must fetch remote simulated results
                    _data = self._fetch_remote_pulser_sim_results(results, metadata)

            # this branch supports legacy wait=True payloads,
            # for example ['{"counter": {...}}']
            case list() | tuple():
                _data = self._fetch_legacy_payload_results(results)

            # this branch is for counts dictionary, which can be used for both local and remote results
            case dict():
                # if the metadata includes "batch", it cines from remote execution
                if metadata is not None and "batch" in metadata:
                    _data = self._fetch_cloud_results(results, metadata)
                else:  # Local execution with direct counts dictionary
                    _data = self._fetch_counter_results(results)

            case None:  # this branch is for remote execution with no direct results
                _data = self._fetch_cloud_results(results, metadata)

            case _:
                raise ValueError(
                    f"Unknown results format. Received {results} of type {type(results)}."
                )

        # feed the data bin into the sampler result with the metadata
        _results: list[SamplerPubResult] = [SamplerPubResult(data=_data)]

        self._update_metadata(
            metadata=metadata,
            backend_name=backend_name,
            job_id=job_id,
        )

        super().__init__(_results, metadata)
        self._backend_name = backend_name

    @classmethod
    def _get_counts(
        cls, results: SimulationResults | Results, metadata: dict[str, Any]
    ) -> Counter | dict[str, int | float]:
        """Get counts from results (pulser's SimulationResults or Results)."""

        if isinstance(results, SimulationResults):

            if metadata["shots"] is None:
                return results.sample_final_state()

            return results.sample_final_state(N_samples=metadata["shots"])

        if isinstance(results, Results):

            if metadata.get("config"):
                obs = metadata["config"].observables[0]
                times = results.get_result_times(obs)
                return results.get_result(obs, times[-1])

        raise ValueError("results must be a SimulationResults or Results.")

    def _fetch_local_sim_results(
        self, results: SimulationResults | Results, metadata: dict[str, Any]
    ) -> DataBin:
        """
        Fetch local simulation results, either from SimulationResults or Results.
        """

        _data = DataBin(counts=self._get_counts(results, metadata))
        metadata["shots"] = int(sum(_data.counts.values()))  # pylint: disable=E1101
        return _data

    @classmethod
    def _fetch_remote_pulser_sim_results(
        cls, results: RemoteResults, metadata: dict[str, Any]
    ) -> DataBin:
        """To fetch remote results from emulators via PasqalCloud."""

        # a simple loop to wait for the job to finish running
        while results.get_batch_status() in {BatchStatus.PENDING, BatchStatus.RUNNING}:
            time.sleep(metadata.get("sleep_sec", None) or 10)

        def get_result() -> DataBin:
            """getting results from remote once the batch finishes"""

            match results.get_batch_status():

                case BatchStatus.DONE:
                    return DataBin(counts=results.results[0].sampling_dist)

                case BatchStatus.CANCELED:
                    raise ValueError("Remote execution was canceled.")

                case BatchStatus.TIMED_OUT:
                    raise ValueError("Remote execution timed out.")

                case BatchStatus.ERROR:
                    raise ValueError("Remote execution error.")

                case BatchStatus.PAUSED:
                    while results.get_batch_status() in {
                        BatchStatus.PENDING,
                        BatchStatus.RUNNING,
                        BatchStatus.PAUSED,
                    }:
                        time.sleep(metadata.get("sleep_sec", None) or 10)
                        return get_result()

                case _:
                    raise NotImplementedError()

            raise NotImplementedError()

        return get_result()

    @classmethod
    def _fetch_cloud_results(
        cls, _results: dict[str, Any] | None, metadata: dict
    ) -> DataBin:
        """
        To fetch results from `pasqal_cloud.SDK` connections. Used by QPU and
        some remote emulators.
        """

        batch: PasqalBatchData = metadata["batch"]

        # get job object to retrieve status and result
        job_obj: PasqalJobData = batch.ordered_jobs[-1]

        if job_obj.status == "DONE":
            return cls._fetch_counter_results(job_obj.result)

        while job_obj.status in {"PENDING", "RUNNING"}:
            batch.refresh()
            time.sleep(metadata.get("sleep_sec", None) or 15)

            if job_obj.status == "DONE":
                return cls._fetch_counter_results(job_obj.result)

            if job_obj.status in {"TIMED_OUT", "ERROR"}:
                break

        raise ValueError(
            "Something went wrong. Please check the cloud project page for more information."
        )

    @classmethod
    def _fetch_counter_results(cls, results: Mapping[str, Any] | Any) -> DataBin:
        """Build a data bin from a direct counts dictionary."""
        if not isinstance(results, Mapping):
            raise ValueError("results must include a dictionary of counts.")
        counts = results.get("counter", results.get("counts", results))
        if not isinstance(counts, dict):
            raise ValueError("results must include a dictionary of counts.")
        return DataBin(counts=Counter(counts))

    @classmethod
    def _fetch_legacy_payload_results(cls, results: list[Any] | tuple[Any, ...]) -> DataBin:
        """Build a data bin from legacy wait=True payload lists."""

        if not results:
            raise ValueError("results list must contain at least one payload.")

        payload = results[0]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as err:
                raise ValueError("results payload is not valid JSON.") from err

        if not isinstance(payload, Mapping):
            raise ValueError("results payload must be a dictionary.")

        return cls._fetch_counter_results(payload)

    @classmethod
    def _fetch_qpu_results(
        cls, results: RemoteResults, metadata: dict[str, Any]
    ) -> DataBin:
        """To fetch remote results from QPU via PasqalCloud."""
        raise NotImplementedError()

    @staticmethod
    def _update_metadata(metadata: dict[str, Any], **kwargs: Any) -> None:
        """Update the metadata to match qiskit's Result metadata signature."""

        for key, value in kwargs.items():
            metadata[key] = value

    def backend_name(self) -> str:
        """The backend name as str."""
        return self._backend_name

    def to_dict(self) -> dict[str, Any]:
        """To return a dictionary containing all the result metadata."""

        result = {"backend_name": self.backend_name(), "results": self._pub_results}
        result.update(self._metadata)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PasqalResult":
        """Create a result from a dictionary."""

        _data = copy.copy(data)
        _data["results"] = [ExperimentResult.from_dict(x) for x in _data.pop("results")]
        return cls(**_data)
