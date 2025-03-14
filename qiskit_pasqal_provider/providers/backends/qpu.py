"""PasqalCloud remote backend"""

from typing import Any, Union

from qiskit import QuantumCircuit
from qiskit.providers import Options
from qiskit.pulse import Schedule, ScheduleBlock
from pulser import QPUBackend as PasqalQPUBackend, Sequence as PasqalSequence
from pulser_pasqal import PasqalCloud

from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.pulse_utils import PasqalRegister, to_pulser
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.jobs import PasqalJob
from qiskit_pasqal_provider.providers.backend_base import PasqalBackend


class QPUBackend(PasqalBackend):
    """QPU backend"""

    def __init__(self, remote_config: RemoteConfig):
        """initialize and instantiate PasqalCloud."""
        super().__init__()
        # check whether pulser's `AnalogDevice` is compatible with QPU
        self._target = PasqalTarget(device="pasqal_device")
        self._cloud = PasqalCloud(**remote_config)

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
        register: PasqalRegister | None = None,
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

        # define a proper code later
        seq = PasqalSequence(register, self.target.device)
        seq.declare_channel("rydberg_global", "rydberg_global")

        pulser_pulses = to_pulser(run_input)
        for pulse, channel in pulser_pulses:
            seq.add(pulse, channel)

        _qpu = PasqalQPUBackend(sequence=seq, connection=self._cloud)

        raise NotImplementedError("QPU backend is not fully implemented yet.")
