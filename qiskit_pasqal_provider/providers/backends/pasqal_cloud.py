"""PasqalCloud remote backend"""
from qiskit_pasqal_provider.providers.backend_base import PasqalRemoteBackend

try:
    from pulser_pasqal import PasqalCloud
except ImportError:
    raise ImportError(
        "'pulser-pasqal' package not found. Please install it through 'pip install pulser-pasqal'."
    )


class PasqalCloudBackend(PasqalRemoteBackend):
    pass
