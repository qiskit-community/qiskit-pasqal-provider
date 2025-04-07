"""Overall util classes and functions"""

from enum import Enum
from typing import Mapping, Optional, Protocol, Any

from pasqal_cloud import TokenProvider, Endpoints, Auth0Conf


class StrEnum(str, Enum):
    """
    Provide a StrEnum similar to `enum`'s `StrEnum` that is not
    available on previous versions of python (<3.11)
    """

    def __str__(self) -> str:
        """Used when dumping enum fields in a schema."""
        ret: str = self.value
        return ret

    @classmethod
    def list(cls) -> list[str]:
        """list the defined attributes as enum fields"""
        return [c.value for c in cls]


class RemoteConfig(Mapping):
    """Remote configuration class for Pasqal provider access."""

    def __init__(
        self,
        username: str = "",
        password: str = "",
        project_id: str = "",
        token_provider: Optional[TokenProvider] = None,
        endpoints: Optional[Endpoints] = None,
        auth0: Optional[Auth0Conf] = None,
        webhook: Optional[str] = None,
    ):
        """
        A data wrapper class for accessing Pasqal's remote backend.

        Args:
            username: email of the user to login. Optional.
            password: password of the user to login. Optional, but
                must be present if `username` is provided.
            project_id: ID of the owner project of the batch. Optional.
            token_provider: the token provider for alternative log-in method.
                Optional, but can be used to replace `username` log-in method.
            endpoints: endpoints targeted of the public APIs.
            auth0: `Auth0Config` instance to define the auth0 tenant to target.
            webhook: webhook where the job results are automatically sent to.
        """

        self.username = username
        self.password = password
        self.project_id = project_id
        self.token_provider = token_provider
        self.endpoints = endpoints
        self.auth0 = auth0
        self.webhook = webhook

    def __getitem__(self, x):
        return self.__dict__[x]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)


class PasqalEmulator(Protocol):
    """A protocol class to account for generic Pasqal emulators."""

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        A run method that must exist for emulators.
        """
