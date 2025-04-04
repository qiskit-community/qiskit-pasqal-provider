"""Base file for Pasqal job class (to avoid circular import)"""

from abc import ABC

from qiskit.primitives import BasePrimitiveJob
from qiskit.providers import JobStatus

from qiskit_pasqal_provider.providers.result import PasqalResult


class PasqalJob(BasePrimitiveJob[PasqalResult, JobStatus], ABC):
    """ABC for Pasqal Jobs"""
