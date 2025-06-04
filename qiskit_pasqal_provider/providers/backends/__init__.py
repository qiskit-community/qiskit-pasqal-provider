"""Pasqal backends"""

from sys import platform

from .qutip import QutipEmulatorBackend
from .local import PasqalLocalBackend
from .remote import PasqalRemoteBackend


__all__ = [
    "QutipEmulatorBackend",
    "PasqalLocalBackend",
    "PasqalRemoteBackend",
]

if platform not in ["win32", "cygwin"]:
    from .emu_mps import EmuMpsBackend

    __all__.append("EmuMpsBackend")
