"""Test the provider functionalities"""

import pytest

from qiskit_pasqal_provider.providers.backends.emu_free import EmuFreeBackend
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.utils import RemoteConfig
from qiskit_pasqal_provider.providers.backends.qutip import QutipEmulatorBackend


def test_provider_empty_remote() -> None:
    """test provider instance attributes and methods on empty remote_config"""

    provider = PasqalProvider()

    assert provider.remote_config is None
    assert isinstance(provider.get_backend("qutip"), QutipEmulatorBackend)

    with pytest.raises(AssertionError):
        provider.get_backend("remote-emu-free")


def test_provider_with_remote() -> None:
    """test provider instance attributes and methods with remote_config"""

    remote_config = RemoteConfig()
    provider = PasqalProvider(remote_config)

    assert provider.remote_config == remote_config
    assert isinstance(provider.get_backend("remote-emu-free"), EmuFreeBackend)
    assert isinstance(provider.get_backend("qutip"), QutipEmulatorBackend)


def test_provider_invalid_backend() -> None:
    """test provider instance for invalid backend"""

    provider = PasqalProvider()

    with pytest.raises(ValueError):
        provider.get_backend("remote-qutip")
