"""Pasqal's result class tools"""

from qiskit.primitives import SamplerPubResult, PrimitiveResult


class Result(PrimitiveResult[SamplerPubResult]):
    """Pasqal Result class"""
