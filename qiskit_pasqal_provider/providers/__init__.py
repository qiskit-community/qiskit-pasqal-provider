"""
=================================================================
Qiskit Pasqal Provider (:mod:`qiskit_pasqal_provider.providers`)
=================================================================

.. currentmodule:: qiskit_pasqal_provider.providers


Qiskit Pasqal Provider classes and functions
=============================================

.. autosummary::
    :toctree: ../stubs/

    HamiltonianGate
    dumps_qpp_openqasm3
    loads_qpp_openqasm3
    PasqalProvider
    SamplerV2
"""

# Explicit `as X` aliases mark intentional public re-exports for Ruff (F401).
from .gate import (
    HamiltonianGate as HamiltonianGate,
    dumps_qpp_openqasm3 as dumps_qpp_openqasm3,
    loads_qpp_openqasm3 as loads_qpp_openqasm3,
)
from .provider import PasqalProvider as PasqalProvider
from .sampler import SamplerV2 as SamplerV2
