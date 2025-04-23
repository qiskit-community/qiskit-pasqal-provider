"""Pasqal's result class tools"""

import copy
import time
from typing import Any

from pulser.backend.remote import RemoteResults, BatchStatus
from pulser_simulation.simresults import SimulationResults

from qiskit.primitives import SamplerPubResult, PrimitiveResult, DataBin
from qiskit.result.models import ExperimentResult


class PasqalResult(PrimitiveResult[list[ExperimentResult]]):
    """To hold and convert Pasqal results to Qiskit Results."""

    def __init__(
        self,
        backend_name: str,
        job_id: str,
        results: SimulationResults | RemoteResults,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Constructor for results from Pasqal emulators and QPUs.

        Args:
            backend_name: Backend name
            results: Pulser results from emulator or QPU
            metadata: Metadata that is common to all the results, such as `backend_version`,
                `shots`, `qobj_id`, `job_id`, `success`
        """

        _data: DataBin

        match results:

            case SimulationResults():
                _data = self._fetch_sim_results(results, metadata)

            case RemoteResults():
                _data = self._fetch_remote_results(results, metadata)

            case _:
                raise ValueError("results must be either locally simulated or remote ones.")

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
    def _fetch_sim_results(cls, results: SimulationResults, metadata: dict[str, Any]) -> DataBin:
        """"""
        # get either a user-defined number of shots (number of samples) or emulator default
        if metadata["shots"] is None:
            _data = DataBin(counts=results.sample_final_state())
            metadata["shots"] = int(sum(_data.counts.values()))  # pylint: disable=E1101

        else:
            _data = DataBin(
                counts=results.sample_final_state(N_samples=metadata["shots"])
            )

        return _data

    @classmethod
    def _fetch_remote_results(cls, results: RemoteResults, metadata: dict[str, Any]) -> DataBin:
        """To fetch remote results from PasqalCloud (emulator and QPU)."""

        # a simple loop to wait for the job to finish running
        while results.get_batch_status() in {BatchStatus.PENDING, BatchStatus.RUNNING}:
            time.sleep(metadata.get("sleep_sec", None) or 10)

        def get_result() -> DataBin:
            """getting results from remote once the batch finishes"""

            match status := results.get_batch_status():

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
                        BatchStatus.PAUSED
                    }:
                        time.sleep(metadata.get("sleep_sec", None) or 10)
                        return get_result()

                case _:
                    raise NotImplementedError()

            raise NotImplementedError()

        return get_result()

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
