"""EMU-MPS backend."""

# pylint: disable=import-outside-toplevel

import uuid
from sys import platform
from typing import Any

from qiskit import QuantumCircuit
from qiskit.providers import Options

from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend,
    PasqalBackendType,
    PasqalJob,
)
from qiskit_pasqal_provider.providers.jobs import PasqalLocalJob
from qiskit_pasqal_provider.providers.pulse_utils import (
    get_register_from_circuit,
    gen_seq,
)
from qiskit_pasqal_provider.providers.target import PasqalTarget


class EmuMpsBackend(PasqalBackend):
    """PasqalEmuMpsBackend."""

    _version: str = "0.1.0"
    backend_name = PasqalBackendType.EMU_MPS

    def __init__(self, target: PasqalTarget, **options: Any):
        """
        Defines the EMU-MPS backend instance.

        Args:
            target (PasqalTarget): the Pasqal target instance
            **options: additional configuration options for the backend
        """
        # super().__init__(target=target, backend="emu-mps")
        name = self.__class__.__name__
        super().__init__(name=name, **options)
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

        analog_register = get_register_from_circuit(run_input)

        seq = gen_seq(
            analog_register=analog_register,
            device=self.target.device,
            circuit=run_input,
        )

        if values:
            seq = seq.build(**values)

        if platform not in ["win32", "cygwin"]:
            from emu_mps import MPSBackend, MPSConfig, BitStrings

            bitstrings = BitStrings() if shots is None else BitStrings(num_shots=shots)
            config = MPSConfig(observables=[bitstrings])
            self._executor = MPSBackend(seq, config=config)

            job_id = str(uuid.uuid4())

            job = PasqalLocalJob(
                backend=self,
                job_id=job_id,
                shots=shots,
                qobj_id=job_id,
                backend_version=self._version,
            )
            job.submit()
            return job

        raise ImportError("EMU-MPS is not supported by Windows.")
