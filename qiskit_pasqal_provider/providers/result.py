"""Pasqal result conversion helpers."""

import json
import time
import warnings
from collections.abc import Mapping
from typing import Any

from pasqal_cloud.batch import Batch as PasqalBatchData
from pasqal_cloud.job import Job as PasqalJobData
from pulser.backend import Results
from pulser.backend.remote import BatchStatus, RemoteResults
from qiskit.primitives import BitArray, DataBin, PrimitiveResult, SamplerPubResult


class PasqalDataBin(DataBin):
    """Sampler data with the bitstrings in `meas`, a BitArray in Qiskit's bit order."""

    __slots__ = ()

    @property
    def counts(self) -> dict[str, int]:
        """Deprecated: the counts in Pulser's bit order (atom 0 leftmost)."""
        warnings.warn(
            "'data.counts' is deprecated, use 'data.meas.get_counts()', whose bitstrings are "
            "in Qiskit's order: qubit 0 is the rightmost bit.",
            DeprecationWarning,
            stacklevel=2,
        )
        return {k[::-1]: v for k, v in self["meas"].get_counts().items()}


def _data_bin(counts: Mapping[str, int]) -> DataBin:
    """Build sampler data from Pulser counts, whose leftmost bit is atom 0."""
    num_bits = len(next(iter(counts)))
    qiskit_counts = {k[::-1]: v for k, v in counts.items()}
    return PasqalDataBin(meas=BitArray.from_counts(qiskit_counts, num_bits=num_bits))


def _get_counts(results: Any, metadata: dict[str, Any]) -> Mapping[str, int]:
    """Get counts from pulser simulation results."""
    if isinstance(results, Results):
        if metadata.get("config"):
            obs = metadata["config"].observables[0]
            times = results.get_result_times(obs)
            return results.get_result(obs, times[-1])

    raise ValueError("results must be a Results with a config.")


def _fetch_remote_pulser_sim_results(
    results: RemoteResults, metadata: dict[str, Any]
) -> DataBin:
    """Fetch remote results from emulators via PasqalCloud."""

    while results.get_batch_status() in {BatchStatus.PENDING, BatchStatus.RUNNING}:
        time.sleep(metadata.get("sleep_sec", None) or 10)

    def get_result() -> DataBin:
        match results.get_batch_status():
            case BatchStatus.DONE:
                return _data_bin(results.results[0].final_bitstrings)
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
    return _data_bin(counts)


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

    match results:
        case Results():
            data = _data_bin(_get_counts(results, metadata))
            metadata["shots"] = data["meas"].num_shots
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
