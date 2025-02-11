"""Defines the wrappers for pulser layout classes"""

from abc import ABC
from numpy.typing import ArrayLike
from pulser.register.register_layout import RegisterLayout
from pulser.register.special_layouts import (
    TriangularLatticeLayout,
    SquareLatticeLayout,
    RectangularLatticeLayout,
)


class PasqalLayout(ABC):
    """Just a base class for checking pasqal layout purposes"""


class FreeLayout(RegisterLayout, PasqalLayout):
    """FreeLayout class. Can be used to define an arbitrary layout."""

    def __init__(self, layout: ArrayLike, slug: str | None = None):
        """
        Create an arbitrary layout for analog registers.

        Args:
            layout (ArrayLike): arbitrary layout that must be array-like type.
            slug (str, optional): Optional slug for layout identification.
        """
        super().__init__(trap_coordinates=layout, slug=slug)


class TriangularLayout(TriangularLatticeLayout):
    """TriangularLayout class. Can be used to define an arbitrary layout."""

    def __init__(self, n_traps: int, spacing: float):
        """
        Create a triangular layout for analog registers.

        Args:
            n_traps (int): number of traps (qubits) to be chosen
            spacing (float): spacing between traps
        """
        super().__init__(n_traps=n_traps, spacing=spacing)


class RectangularLayout(RectangularLatticeLayout, PasqalLayout):
    """RectangularLayout class. Can be used to define an arbitrary layout."""

    def __init__(self, rows: int, columns: int, col_spacing: float, row_spacing: float):
        """
        Create a rectangular layout for analog registers.

        Args:
            rows (int): number of rows in the layout
            columns (int): number of columns in the layout
            col_spacing (float): spacing between columns
            row_spacing (float): spacing between rows
        """
        super().__init__(
            rows=rows, columns=columns, col_spacing=col_spacing, row_spacing=row_spacing
        )


class SquareLayout(SquareLatticeLayout, PasqalLayout):
    """SquareLayout class. Can be used to define an arbitrary layout."""

    def __init__(self, rows: int, columns: int, spacing: float):
        """
        Create a square layout for analog registers.

        Args:
            rows (int): number of rows in the layout
            columns (int): number of columns in the layout
            spacing (float): spacing between traps
        """
        super().__init__(rows=rows, columns=columns, spacing=spacing)
