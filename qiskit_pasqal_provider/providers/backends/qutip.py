"""QuTiP backend"""

import copy
import uuid
from typing import Any, Union

from pulser import Register, Sequence as PasqalSequence
from pulser_simulation import QutipEmulator
from qiskit import QuantumCircuit
from qiskit.providers import Options
from qiskit.pulse import Schedule, ScheduleBlock

from qiskit_pasqal_provider.providers.backend_base import PasqalBackend
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.jobs import PasqalJob, PasqalLocalJob
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister, to_pulser


class QutipEmulatorBackend(PasqalBackend):
    """QutipEmulatorBackend to emulate pulse sequences using QuTiP."""

    def __init__(self, target: PasqalTarget, **options: Any):
        """

        Args:
            target (PasqalTarget): The target of the pulse sequence.
            **options: additional configuration options
        """

        self.backend_name = self.__class__.__name__
        super().__init__(name=self.backend_name, **options)
        self.backend = "qutip"
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

        assert register is not None, "register cannot be None"

        # Run a program on Pasqal backend
        if isinstance(run_input, QuantumCircuit):
            seq = PasqalSequence(register, self.target.device)
            seq.declare_channel("rydberg_global", "rydberg_global")

            pulser_pulses = to_pulser(run_input)
            for pulse, channel in pulser_pulses:
                seq.add(pulse, channel)

            # initialise the backend from sequence.
            # In the sequence the register and device is encoded
            # we can imagine moving that to the Qiskit Backend
            emulator = QutipEmulator.from_sequence(seq)
            backend = copy.deepcopy(self)
            job_id = str(uuid.uuid4())
            return PasqalLocalJob(backend, job_id, emulator)

        if isinstance(run_input, ScheduleBlock):
            raise NotImplementedError("ScheduleBlocks not yet supported")

        if isinstance(run_input, Schedule):
            raise NotImplementedError("Schedule not supported")

        raise ValueError("run_input must be Schedule, ScheduleBlock or QuantumCircuit")
