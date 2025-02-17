"""Overall util classes and functions"""

from enum import Enum


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
