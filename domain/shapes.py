"""Shape vocabulary and per-shape dimension requirements.

Kept deliberately simple: one ShapeDimensions dataclass plus a lookup of which
fields each shape requires. The generator (Milestone 2+) enforces the
requirements; this module only provides the vocabulary and the check helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ShapeType(Enum):
    """Shapes supported by the MVP."""

    CIRCLE = "circle"
    CYLINDER = "cylinder"
    BALL = "ball"


@dataclass(frozen=True)
class ShapeDimensions:
    """User-supplied target dimensions in centimeters.

    diameter_cm: required by all three shapes.
    height_cm:   required only by the cylinder.
    """

    diameter_cm: float | None = None
    height_cm: float | None = None

    def __post_init__(self) -> None:
        if self.diameter_cm is not None and self.diameter_cm <= 0:
            raise ValueError("diameter_cm must be positive when provided")
        if self.height_cm is not None and self.height_cm <= 0:
            raise ValueError("height_cm must be positive when provided")

    def missing_fields(self, shape: ShapeType) -> list[str]:
        """Return the names of required-but-missing fields for this shape."""
        required = REQUIRED_DIMENSIONS[shape]
        values = {"diameter_cm": self.diameter_cm, "height_cm": self.height_cm}
        return [name for name in required if values[name] is None]


REQUIRED_DIMENSIONS: dict[ShapeType, tuple[str, ...]] = {
    ShapeType.CIRCLE: ("diameter_cm",),
    ShapeType.BALL: ("diameter_cm",),
    ShapeType.CYLINDER: ("diameter_cm", "height_cm"),
}
