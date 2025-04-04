"""EMU-MPS backend."""

from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import Options

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.job_base import PasqalJob


class EmuMpsBackend(PasqalBackend):
    """PasqalEmuMpsBackend."""

    def __init__(self, target: PasqalTarget, **options: Any):
        """
        defines the EMU-MPS backend instance.

        Args:
            target (PasqalTarget): the Pasqal target instance
            **options: additional configuration options for the backend
        """
        # super().__init__(target=target, backend="emu-mps")
        self.backend_name = self.__class__.__name__
        super().__init__(name=self.backend_name, **options)
        self.backend = "emu-mps"
        self._target = target
        self._layout = self.target.layout

    @property
    def target(self) -> PasqalTarget:
        return self._target

    @property
    def max_circuits(self) -> None:
        return None

    @classmethod
    def _default_options(cls) -> Options:
        return Options()

    def run(
        self,
        run_input: QuantumCircuit,
        shots: int | None = None,
        values: dict | None = None,
        **options: Any,
    ) -> PasqalJob:
        """
        Run a quantum circuit for a given execution interface, namely `Sampler`.

        Args:
            run_input: the quantum circuit to be run.
            shots: number of shots to run. Optional.
            values: a dictionary containing all the parametric values. Optional.
            **options: extra options to pass to the backend if needed.

        Returns:
            A PasqalJob instance containing the results from the execution interface.
        """
        raise NotImplementedError()
