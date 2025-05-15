"""Sampler base class based on `SamplerV2`."""

from typing import Any, Iterable
from warnings import warn

from qiskit.circuit import QuantumCircuit, Parameter, ParameterExpression
from qiskit.providers.jobstatus import JobStatus
from qiskit.primitives import (
    BaseSamplerV2,
    SamplerPubLike,
    BasePrimitiveJob,
    PrimitiveResult,
    SamplerPubResult,
)

from qiskit_pasqal_provider.providers.abstract_base import PasqalBackend, PasqalJob


class Sampler(BaseSamplerV2):
    """Pasqal's sampler base class."""

    def __init__(self, backend: PasqalBackend):
        self._backend = backend

    @property
    def mode(self) -> None:
        """Sampler mode"""
        warn("'mode' is not a valid method for Pasqal's  Sampler class.", UserWarning)
        return None

    def backend(self) -> PasqalBackend:
        """Method to return the provided backend"""
        return self._backend

    def build(
        self,
        pubs: Iterable[SamplerPubLike],
        *,
        values: dict | None = None
    ) -> PasqalBackend:
        qc, values = self._coerce_pubs(pubs)
        return self._backend.build(qc, values=values)

    @classmethod
    def _coerce_pubs(
        cls, pubs: Iterable[SamplerPubLike]
    ) -> tuple[QuantumCircuit, dict[str, ParameterExpression] | dict]:
        """
        Coerce the pubs into digestible data for backend's run method.

        Args:
            pubs: An iterable of pub-like objects. For example, a list of circuits
                or tuples ``(circuit, parameter_values)``.

        Returns:
            A tuple of circuit and optional parameter values
        """

        if isinstance(pubs, QuantumCircuit):
            return pubs, {}

        if isinstance(pubs, list | tuple):

            if isinstance(pubs[0], tuple):

                if len(pubs[0]) == 1 and isinstance(pubs[0][0], QuantumCircuit):
                    return pubs[0][0], {}

                if (
                    len(pubs[0]) == 2
                    and isinstance(pubs[0][0], QuantumCircuit)
                    and isinstance(pubs[0][1], dict)
                ):

                    return pubs[0][0], _parameter_to_str(pubs[0][1])

            if isinstance(pubs[0], QuantumCircuit):
                return pubs[0], {}

        raise ValueError(
            "'pubs' argument must be a QuantumCircuit "
            "or a tuple of QuantumCircuit and ParameterExpression."
        )

    def run(
        self, pubs: Iterable[SamplerPubLike], *, shots: int | None = None
    ) -> BasePrimitiveJob[PrimitiveResult[SamplerPubResult], JobStatus] | PasqalJob:
        """
        Runs and collects samples from each pub.

        Args:
            pubs: An iterable of pub-like objects. For example, a list of circuits
                  or tuples ``(circuit, parameter_values)``.
            shots: The total number of shots to sample for each sampler pub that does
                   not specify its own shots. If ``None``, the primitive's default
                   shots value will be used, which can vary by implementation.

        Returns:
            The job object of Sampler's result.

        """

        qc, values = self._coerce_pubs(pubs)
        return self._backend.run(run_input=qc, values=values, shots=shots)


def _parameter_to_str(values: dict[Parameter, Any]) -> dict[str, Any]:
    return {k.name:v for k, v in values.items()}
