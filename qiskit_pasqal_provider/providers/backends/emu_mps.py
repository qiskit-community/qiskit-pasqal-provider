"""EMU-MPS backend."""

from typing import Any, Union

from pulser import Register
from qiskit import QuantumCircuit
from qiskit.providers import Options
from qiskit.pulse import Schedule, ScheduleBlock

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.jobs import PasqalJob
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister


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
        run_input: Union[QuantumCircuit, Schedule, ScheduleBlock],
        register: PasqalRegister | Register | None = None,
        **options: Any,
    ) -> PasqalJob:
        """

        Args:
            run_input (QuantumCircuit, Schedule, ScheduleBlock): the block of instructions
                to be run
            register (PasqalRegister): the register to be used in the instruction execution
            **options: additional configuration options for the run

        Returns:
            A PasqalJob instance.
        """
        raise NotImplementedError()
