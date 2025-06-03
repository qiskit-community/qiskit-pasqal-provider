"""Test PasqalResult objects"""

import uuid
from copy import deepcopy

from pasqal_cloud.job import CreateJob, Job
from pulser.backend.remote import RemoteConnection, RemoteResults
from pulser.result import Result

from qiskit_pasqal_provider.providers.result import PasqalResult
from tests import DEFAULT_DICT_RESULT
from tests.conftest import MockSDK


def test_mock_remote_sim_result(
    mock_conn: RemoteConnection, mock_sdk: MockSDK, mock_result: Result
) -> None:
    """Test a mock remote setting to evaluate the result pipeline."""

    batch = mock_sdk.create_batch("", [CreateJob(runs=1000, variables={})])
    metadata = {"batch": batch, "status": None}
    results = RemoteResults(batch.id, connection=mock_conn)
    result = PasqalResult(
        backend_name="MockBackend", job_id="", results=results, metadata=metadata
    )
    counts = result[0].data.counts

    assert counts == mock_result.sampling_dist


def test_mock_cloud_sim_result(mock_sdk: MockSDK, mock_result: Result) -> None:
    """Test a mock remote setting to evaluate the result pipeline."""

    batch = mock_sdk.create_batch("", [CreateJob(runs=1000, variables={})])

    job = Job(
        runs=1000,
        batch_id=batch.id,
        id=str(uuid.uuid4()),
        project_id="",
        status="DONE",
        created_at="",
        updated_at="",
        _client=None,
    )
    job._full_result = {  # pylint: disable=protected-access
        "counter": deepcopy(DEFAULT_DICT_RESULT),
        "raw": [],
    }

    batch._ordered_jobs = [job]  # pylint: disable=protected-access
    metadata = {"batch": batch, "status": None}

    result = PasqalResult(
        backend_name="MockBackend",
        job_id="",
        results=deepcopy(DEFAULT_DICT_RESULT),
        metadata=metadata,
    )
    counts = result[0].data.counts

    assert counts == mock_result.sampling_dist
