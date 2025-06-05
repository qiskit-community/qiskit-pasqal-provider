"""Provider implementation"""

from typing import Any

from qiskit_pasqal_provider.providers.abstract_base import (
    PasqalBackend,
    PasqalBackendType,
)
from qiskit_pasqal_provider.providers.backends.local import PasqalLocalBackend
from qiskit_pasqal_provider.providers.backends.remote import PasqalRemoteBackend
from qiskit_pasqal_provider.providers.target import PasqalTarget
from qiskit_pasqal_provider.utils import RemoteConfig


class PasqalProvider:
    """Pasqal provider class"""

    remote_config: RemoteConfig | None

    def __init__(
        self,
        remote_config: RemoteConfig | None = None,
        **options: Any,
    ):
        """
        Defines a Pasqal provider that provides access to a backend. It can be
        either local or remote.

        Args:
            remote_config: RemoteConfig instance for remote backends only. Optional.
            **options: any other relevant optional parameters that a backend may use.
        """

        if remote_config is None:
            self.remote_config = None

        else:
            self.remote_config = remote_config

        self.options = options

    def get_backend(
        self, backend_name: str, target: PasqalTarget | None = None
    ) -> PasqalBackend:
        """
        Retrieves a backend instance from a given backend name string. It will
        try to look for it on the local backends first, then on remote backends.
        If nothing is found, an exception is raised. For remote backends,
        `remote_config` data is used (provided at the `PasqalProvider` instance
        creation).

        Args:
            backend_name: a string containing the name of the desired backend.
            target: the optional Pasqal target device.

        Returns:
            A PasqalBackend instance. It will be a local or remote backend
                depending on the specifications of the backend.
        """

        if backend_name in PasqalBackendType:

            try:
                _backend = PasqalLocalBackend(
                    backend=backend_name, target=target, **self.options
                )

            except NotImplementedError:

                try:

                    assert (
                        self.remote_config is not None
                    ), "'remote_config' must be provided to access remote backends."

                    _backend = PasqalRemoteBackend(
                        backend=backend_name,
                        remote_config=self.remote_config,
                        target=target,
                        **self.options,
                    )

                except NotImplementedError as exc:
                    raise ValueError(f"{backend_name} is not a valid backend") from exc

            return _backend

        raise ValueError(f"{backend_name} is not a valid backend")
