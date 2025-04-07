"""PasqalCloud remote backend"""

from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import Options
from pulser import QPUBackend as PasqalQPUBackend
from pulser_pasqal import PasqalCloud

from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.pulse_utils import (
    get_register_from_circuit,
    gen_seq,
)
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.providers.job_base import PasqalJob
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

        analog_register = get_register_from_circuit(run_input)

        # get a sequence
        seq = gen_seq(
            analog_register=analog_register,
            device=self.target.device,
            circuit=run_input,
        )

        _qpu = PasqalQPUBackend(sequence=seq, connection=self._cloud)

        raise NotImplementedError("QPU backend is not fully implemented yet.")
