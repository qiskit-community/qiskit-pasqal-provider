"""Pasqal result conversion helpers."""

import json
import time
from collections import Counter
from collections.abc import Mapping
from typing import Any

from pasqal_cloud.batch import Batch as PasqalBatchData
from pasqal_cloud.job import Job as PasqalJobData
from pulser.backend import Results
from pulser.backend.remote import BatchStatus, RemoteResults
from qiskit.primitives import DataBin, PrimitiveResult, SamplerPubResult

try:
    from pulser_simulation.simresults import SimulationResults as _SimulationResults
except ImportError:
    _SimulationResults = None


def _get_counts(
    results: Any, metadata: dict[str, Any]
) -> Counter | dict[str, int | float]:
    """Get counts from pulser simulation results."""
    if _SimulationResults is not None and isinstance(results, _SimulationResults):
        if metadata["shots"] is None:
            return results.sample_final_state()
        return results.sample_final_state(N_samples=metadata["shots"])

    if isinstance(results, Results):
        if metadata.get("config"):
            obs = metadata["config"].observables[0]
            times = results.get_result_times(obs)
            return results.get_result(obs, times[-1])

    raise ValueError("results must be a SimulationResults or Results.")


def _fetch_remote_pulser_sim_results(
    results: RemoteResults, metadata: dict[str, Any]
) -> DataBin:
    """Fetch remote results from emulators via PasqalCloud."""

    while results.get_batch_status() in {BatchStatus.PENDING, BatchStatus.RUNNING}:
        time.sleep(metadata.get("sleep_sec", None) or 10)

    def get_result() -> DataBin:
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


def _fetch_cloud_results(_results: dict[str, Any] | None, metadata: dict) -> DataBin:
    """Fetch results from `pasqal_cloud.SDK` connections."""

    batch: PasqalBatchData = metadata["batch"]
    job_obj: PasqalJobData = batch.ordered_jobs[-1]

    if job_obj.status == "DONE":
        return _fetch_counter_results(job_obj.result)

    while job_obj.status in {"PENDING", "RUNNING"}:
        batch.refresh()
        time.sleep(metadata.get("sleep_sec", None) or 15)

        if job_obj.status == "DONE":
            return _fetch_counter_results(job_obj.result)

        if job_obj.status in {"TIMED_OUT", "ERROR"}:
            break

    raise ValueError(
        "Something went wrong. Please check the cloud project page for more information."
    )


def _fetch_counter_results(results: Mapping[str, Any] | Any) -> DataBin:
    """Build a data bin from a direct counts dictionary."""
    if not isinstance(results, Mapping):
        raise ValueError("results must include a dictionary of counts.")
    counts = results.get("counter", results.get("counts", results))
    if not isinstance(counts, dict):
        raise ValueError("results must include a dictionary of counts.")
    return DataBin(counts=Counter(counts))


def _fetch_legacy_payload_results(results: list[Any] | tuple[Any, ...]) -> DataBin:
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

    return _fetch_counter_results(payload)


def build_primitive_result(
    backend_name: str,
    job_id: str | list[str],
    results: Any,
    metadata: dict[str, Any] | None = None,
) -> PrimitiveResult[SamplerPubResult]:
    """Build a Qiskit PrimitiveResult from Pasqal backend outputs."""
    metadata = {} if metadata is None else dict(metadata)

    if _SimulationResults is not None and isinstance(results, _SimulationResults):
        counts = _get_counts(results, metadata)
        data = DataBin(counts=counts)
        metadata["shots"] = int(sum(data.counts.values()))  # pylint: disable=E1101
        metadata["backend_name"] = backend_name
        metadata["job_id"] = job_id
        return PrimitiveResult([SamplerPubResult(data=data)], metadata)

    match results:
        case Results():
            counts = _get_counts(results, metadata)
            data = DataBin(counts=counts)
            metadata["shots"] = int(sum(data.counts.values()))  # pylint: disable=E1101
        case RemoteResults():
            if backend_name == "qpu":
                raise NotImplementedError()
            data = _fetch_remote_pulser_sim_results(results, metadata)
        case list() | tuple():
            data = _fetch_legacy_payload_results(results)
        case dict():
            if "batch" in metadata:
                data = _fetch_cloud_results(results, metadata)
            else:
                data = _fetch_counter_results(results)
        case None:
            data = _fetch_cloud_results(results, metadata)
        case _:
            raise ValueError(
                f"Unknown results format. Received {results} of type {type(results)}."
            )

    metadata["backend_name"] = backend_name
    metadata["job_id"] = job_id
    return PrimitiveResult([SamplerPubResult(data=data)], metadata)
