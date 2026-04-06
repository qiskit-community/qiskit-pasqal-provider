"""Test provider result conversion helpers."""

import json
import uuid
from copy import deepcopy
from typing import Any, cast

import pytest
from pasqal_cloud.job import CreateJob, Job
from pulser.backend.remote import RemoteConnection, RemoteResults
from pulser.result import Result
from qiskit.primitives import PrimitiveResult
from qiskit.providers.jobstatus import JobStatus

from qiskit_pasqal_provider.providers.jobs import PasqalRemoteJob
from qiskit_pasqal_provider.providers.result import build_primitive_result
from tests import DEFAULT_DICT_RESULT
from tests.conftest import MockSDK


def test_mock_remote_sim_result(
    mock_conn: RemoteConnection, mock_sdk: MockSDK, mock_result: Result
) -> None:
    """Test a mock remote setting to evaluate the result pipeline."""

    batch = mock_sdk.create_batch("", [CreateJob(runs=1000, variables={})])
    metadata = {"batch": batch, "status": None}
    results = RemoteResults(batch.id, connection=mock_conn)
    result = build_primitive_result(
        backend_name="MockBackend", job_id="", results=results, metadata=metadata
    )
    assert isinstance(result, PrimitiveResult)
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
        "serialised_results": None,
    }

    batch._ordered_jobs = [job]  # pylint: disable=protected-access
    metadata = {"batch": batch, "status": None}

    result = build_primitive_result(
        backend_name="MockBackend",
        job_id="",
        results=deepcopy(DEFAULT_DICT_RESULT),
        metadata=metadata,
    )
    counts = result[0].data.counts

    assert counts == mock_result.sampling_dist


def test_counter_result_without_batch_metadata(mock_result: Result) -> None:
    """Test that direct counter payloads produce a PrimitiveResult."""
    result = build_primitive_result(
        backend_name="MockBackend",
        job_id="",
        results={"counter": deepcopy(DEFAULT_DICT_RESULT)},
        metadata={"status": "DONE"},
    )
    counts = result[0].data.counts

    assert counts == mock_result.sampling_dist


def test_legacy_wait_true_payload_list_is_supported(mock_result: Result) -> None:
    """Test that legacy wait=True payload lists produce a PrimitiveResult."""

    payload = json.dumps({"counter": deepcopy(DEFAULT_DICT_RESULT)})
    result = build_primitive_result(
        backend_name="MockBackend",
        job_id="",
        results=[payload],
        metadata={"status": "DONE"},
    )
    counts = result[0].data.counts

    assert counts == mock_result.sampling_dist


def test_mock_cloud_result_rejects_malformed_counter(mock_sdk: MockSDK) -> None:
    """Test that malformed cloud counters fail with a clear error."""

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
        "counter": cast(Any, "not-a-dict"),
        "raw": [],
        "serialised_results": None,
    }

    batch._ordered_jobs = [job]  # pylint: disable=protected-access
    metadata = {"batch": batch, "status": None}

    with pytest.raises(ValueError, match="dictionary of counts"):
        build_primitive_result(
            backend_name="MockBackend",
            job_id="",
            results=deepcopy(DEFAULT_DICT_RESULT),
            metadata=metadata,
        )


def test_remote_job_rejects_multi_job_batch(mock_sdk: MockSDK) -> None:
    """Test that remote jobs enforce a single-job batch contract."""

    class MockBackend:
        """Minimal backend stub to build a PasqalRemoteJob."""

        def __init__(self, executor: MockSDK) -> None:
            self._executor = executor
            self.name = "MockBackend"
            self.emulator = None

        @property
        def executor(self) -> MockSDK:
            """Backend executor."""
            return self._executor

    class MockSequence:
        """Minimal sequence stub for remote job submission."""

        @staticmethod
        def to_abstract_repr() -> str:
            """Serialized sequence placeholder."""
            return ""

    backend = MockBackend(mock_sdk)
    job = PasqalRemoteJob(
        backend=backend,  # type: ignore[arg-type]
        seq=MockSequence(),  # type: ignore[arg-type]
        job_params=[
            CreateJob(runs=1000, variables={}),
            CreateJob(runs=1000, variables={}),
        ],
        wait=False,
    )

    with pytest.raises(ValueError, match="supports exactly one job per batch"):
        job.submit()


def test_remote_job_uses_job_status_for_metadata() -> None:
    """Test remote metadata status is derived from the single job status."""

    class MockBatch:
        """Minimal batch stub with diverging batch/job statuses."""

        def __init__(self) -> None:
            self.status = "RUNNING"
            self.ordered_jobs = [
                type("Job", (), {"id": "job-1", "status": "DONE", "result": {}})()
            ]

        def refresh(self) -> None:
            """No-op refresh."""

    class MockExecutor:
        """Minimal executor stub."""

        @staticmethod
        def create_batch(*_args, **_kwargs) -> MockBatch:
            """Return a deterministic mock batch."""
            return MockBatch()

    class MockBackend:
        """Minimal backend stub to build a PasqalRemoteJob."""

        def __init__(self) -> None:
            self._executor = MockExecutor()
            self.name = "MockBackend"
            self.emulator = None

        @property
        def executor(self) -> MockExecutor:
            """Backend executor."""
            return self._executor

    class MockSequence:
        """Minimal sequence stub for remote job submission."""

        @staticmethod
        def to_abstract_repr() -> str:
            """Serialized sequence placeholder."""
            return ""

    job = PasqalRemoteJob(
        backend=MockBackend(),  # type: ignore[arg-type]
        seq=MockSequence(),  # type: ignore[arg-type]
        job_params=[CreateJob(runs=1000, variables={})],
        wait=False,
    )
    job.submit()

    assert job.metadata["status"] == "DONE"
    assert job.status() == JobStatus.DONE


def test_remote_job_wait_false_is_non_blocking() -> None:
    """Test wait=False submit does not eagerly fetch results."""

    class MockBatch:
        """Minimal batch stub with a running job."""

        def __init__(self) -> None:
            self.ordered_jobs = [
                type("Job", (), {"id": "job-1", "status": "RUNNING", "result": {}})()
            ]

        def refresh(self) -> None:
            """Guard against eager polling in submit."""
            raise AssertionError(
                "submit() should not poll cloud results when wait=False."
            )

    class MockExecutor:
        """Minimal executor stub."""

        @staticmethod
        def create_batch(*_args, **_kwargs) -> MockBatch:
            """Return a running batch."""
            return MockBatch()

    class MockBackend:
        """Minimal backend stub to build a PasqalRemoteJob."""

        def __init__(self) -> None:
            self._executor = MockExecutor()
            self.name = "MockBackend"
            self.emulator = None

        @property
        def executor(self) -> MockExecutor:
            """Backend executor."""
            return self._executor

    class MockSequence:
        """Minimal sequence stub for remote job submission."""

        @staticmethod
        def to_abstract_repr() -> str:
            """Serialized sequence placeholder."""
            return ""

    job = PasqalRemoteJob(
        backend=MockBackend(),  # type: ignore[arg-type]
        seq=MockSequence(),  # type: ignore[arg-type]
        job_params=[CreateJob(runs=1000, variables={})],
        wait=False,
    )
    job.submit()

    assert job.metadata["status"] == "RUNNING"
    assert job.status() == JobStatus.RUNNING
