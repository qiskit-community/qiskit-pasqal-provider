"""fixture for tests."""

import sys
import typing
import json
import uuid
from copy import deepcopy
from typing import Any, Mapping

from unittest.mock import MagicMock
from collections import defaultdict

import numpy as np
import pytest

from pasqal_cloud.batch import Batch
from pasqal_cloud.device import EmulatorType, BaseConfig
from pasqal_cloud.job import CreateJob, Job
from pasqal_cloud.utils.responses import PaginatedResponse
from pasqal_cloud.utils.filters import JobFilters
from pulser import Register as PasqalRegister, Sequence
from pulser.result import Result
from pulser.backend import Results
from pulser.backend.remote import (
    RemoteConnection,
    RemoteResults,
    JobStatus,
    BatchStatus,
)
from pulser.devices import Device

from qiskit_pasqal_provider.providers.gate import InterpolatePoints
from qiskit_pasqal_provider.providers.layouts import (
    SquareLayout,
)
from qiskit_pasqal_provider.providers.target import (
    PasqalDevice,
    AVAILABLE_DEVICES,
    PasqalTarget,
)
from tests import DEFAULT_DICT_RESULT, ATOM_ORDER, NUM_ATOMS


@pytest.fixture
def square_coords() -> list:
    """simple square coordinates."""
    return [(0, 0), (0, 1), (1, 0), (1, 1)]


@pytest.fixture
def null_interpolate_points() -> InterpolatePoints:
    """constant null interpolate points instance."""
    return InterpolatePoints(values=[0.0, 0.0, 0.0])


@pytest.fixture
def constant_interpolate_points() -> InterpolatePoints:
    """constant 'normalized' interpolate points instance."""
    return InterpolatePoints(values=[1.0, 1.0, 1.0, 1.0])


@pytest.fixture
def linear_interpolate_points() -> InterpolatePoints:
    """linear interpolate points instance."""
    return InterpolatePoints(values=[0.0, 1.0 / 3, 2.0 / 3, 1.0])


@pytest.fixture
def bump_interpolate_points() -> InterpolatePoints:
    """bump interpolate points instance."""
    return InterpolatePoints(values=[0.0, 1.0, 1.0, 0.0])


@pytest.fixture
def pasqal_target() -> PasqalTarget:
    """
    fixture for pre-defined pasqal target instance.
    """
    return PasqalTarget(device=AVAILABLE_DEVICES["analog"])


@pytest.fixture
def pasqal_register() -> PasqalRegister:
    """
    fixture for rectangle-shaped Pasqal Register instance.
    """
    return PasqalRegister.rectangle(1, 4, spacing=5, prefix="atom")


@pytest.fixture
def square_register2x2() -> PasqalRegister:
    """
    fixture for square-shaped Pasqal Register instance.
    """
    return PasqalRegister.square(2, spacing=5, prefix="atom")


@pytest.fixture
def pasqal_device() -> PasqalDevice | Device:
    """
    fixture for pulser.devices.AnalogDevice object.
    """
    return AVAILABLE_DEVICES["analog"]


@pytest.fixture
def hybrid_device() -> PasqalDevice | Device:
    """
    fixture for pulser.devices.AnalogDevice object.
    """
    return AVAILABLE_DEVICES["hybrid"]


@pytest.fixture
def square_layout2x2() -> SquareLayout:
    """
    fixture for pulser square layout instance (2x2).
    """
    return SquareLayout(2, 2, spacing=5)


@pytest.fixture
def square_layout1() -> SquareLayout:
    """
    fixture for pulser square layout instance.
    """
    return SquareLayout(7, 4, spacing=5)


class MockServer:
    """A mock server to simulate job progress and manage job states.

    This class keeps track of jobs and their progress to simulate real-world
    execution and status updates. It supports setting and retrieving jobs
    while simulating their progress through internal counters.
    """

    def __init__(self) -> None:
        """Initialize the mock server with empty job data and progress counters."""
        self.jobs: dict[str, Job] = {}
        self.jobs_progress_counter: dict[str, int] = defaultdict(int)
        # Set how many progress steps are needed before each batch is marked as done
        self.max_progress_steps = 3

    def get_job(self, job_id: str) -> Job:
        """Retrieve the job by ID and simulate its progress.

        Args:
            job_id (str): The ID of the job to retrieve.

        Returns:
            Job: The job object after simulating a progress step.
        """
        self._simulate_job_progress_step(job_id)
        return self.jobs[job_id]

    def set_job(self, job: Job) -> None:
        """Store a job in the mock server.

        Args:
            job (Job): The job to store in the server.
        """
        self.jobs[job.id] = job

    def _simulate_job_progress_step(self, job_id: str) -> None:
        """Update in place the job store to simulate progress.

        Check how many times this function has been called for a given
        job and updates its progress accordingly.
        On the first call, the job status is set to RUNNING.
        After self.max_progress_steps, the job status is set to DONE and
        fake results are set.

        Args:
            job_id (str): The ID of the job for which progress is being simulated.
        """
        progress_step = self.jobs_progress_counter[job_id]
        if progress_step == 0:
            self.jobs[job_id].status = "RUNNING"
        if progress_step >= self.max_progress_steps:
            self.jobs[job_id].status = "DONE"
            self.jobs[job_id]._full_result = {  # pylint: disable=protected-access
                "counter": deepcopy(DEFAULT_DICT_RESULT),
                "raw": [],
            }
        self.jobs_progress_counter[job_id] += 1


class MockSDK:
    """Helper class to mock the cloud SDK and skip the API calls.

    Warning: This implements only a small subset of the functions available
        in the cloud SDK; focusing on the functions used by qek.
        This should be extended to support all methods and moved to the
        pasqal-cloud repository so that it can be reused for all future
        libraries using the SDK.
    """

    def __init__(self) -> None:
        self.mock_server = MockServer()

    def get_device_specs_dict(self) -> Any:
        """Retrieve the device specifications from a local JSON file."""
        with open(
            "tests/cloud_fixtures/device_specs.json",
            "r",
            encoding=sys.getfilesystemencoding(),
        ) as f:
            return json.load(f)

    def create_batch(
        self,
        _serialized_sequence: str,
        jobs: list[CreateJob],
        open: bool | None = None,  # pylint: disable=redefined-builtin
        emulator: EmulatorType | None = None,
        configuration: BaseConfig | None = None,
        _wait: bool = False,
    ) -> Batch:
        """Create a batch of jobs and simulate its creation in the mock server."""
        batch_id = str(uuid.uuid4())
        batch = Batch(
            id=batch_id,
            open=bool(open),
            complete=bool(open),
            created_at="",
            updated_at="",
            device_type=emulator if emulator else "FRESNEL",
            project_id="",
            user_id="",
            status="DONE",
            jobs=[
                {
                    **j,
                    "batch_id": batch_id,
                    "id": str(uuid.uuid4()),
                    "project_id": "",
                    "status": "DONE",
                    "created_at": "",
                    "updated_at": "",
                }
                for j in jobs
            ],
            configuration=configuration,
            _client=MagicMock(),
        )

        self.mock_server.set_job(batch.ordered_jobs[0])
        return batch

    def get_jobs(self, filters: JobFilters) -> PaginatedResponse:
        """Retrieve jobs based on filters, simulating the SDK's get_jobs call."""
        items: list[Job] = []

        assert isinstance(filters.id, list)
        for job_id in filters.id:
            items.append(self.mock_server.get_job(str(job_id)))

        return PaginatedResponse(
            results=items,
            total=len(items),
            offset=0,
        )


class MockConnection(RemoteConnection):
    """MockConnection class to emulate `pulser` RemoteConnection"""

    def __init__(self):
        """Define MockConnection"""
        self.results = [MockResult()]
        self._job_id = lambda batch_id: str(uuid.uuid3(uuid.NAMESPACE_OID, batch_id))

    def submit(
        self,
        sequence: Sequence,
        wait: bool = False,
        open: bool = True,  # pylint: disable=redefined-builtin
        batch_id: str | None = None,
        **kwargs: Any,
    ) -> RemoteResults:
        """To submit the MockConnection"""
        raise NotImplementedError()

    def _fetch_result(
        self, batch_id: str, job_ids: list[str] | None
    ) -> typing.Sequence[Results]:
        """Fetching mock results"""
        return self.results

    def _query_job_progress(
        self, batch_id: str
    ) -> Mapping[str, tuple[JobStatus, Results | None]]:
        """Querying mock job progress"""
        return {self._job_id(batch_id): (JobStatus.DONE, self.results[0])}

    def _get_batch_status(self, batch_id: str) -> BatchStatus:
        """Getting mock batch status"""
        return BatchStatus.DONE

    def supports_open_batch(self) -> bool:
        """Whether to support open batch"""
        return False

    def _get_job_ids(self, batch_id: str) -> list[str]:
        """Get mock job ids"""
        return [self._job_id(batch_id)]


class MockResult(Result):
    """MockResult to emulate pulser Result"""

    def __init__(self):
        """"""
        atom_order = ATOM_ORDER
        super().__init__(meas_basis="", atom_order=atom_order)

    @property
    def sampling_errors(self) -> dict[str, float]:
        return {}

    def _weights(self) -> np.ndarray:
        """Get weights as numpy array"""

        weights = np.zeros(NUM_ATOMS)
        weights[9] = 50
        weights[11] = 25
        return weights


@pytest.fixture
def mock_conn() -> RemoteConnection:
    """Fixture for RemoteConnection instance"""
    return MockConnection()


@pytest.fixture
def mock_sdk() -> MockSDK:
    """Fixture for MockSDK instance"""
    return MockSDK()


@pytest.fixture
def mock_result() -> Result:
    """Fixture for MockResult instance"""
    return MockResult()
