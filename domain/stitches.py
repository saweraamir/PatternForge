"""Stitch vocabulary with explicit consumed-vs-produced semantics.

Each stitch type defines how many EXISTING stitches it consumes (worked into,
from the previous round or the magic ring) and how many NEW stitches it
produces (added to the current round). This single source of truth is shared
by both the generator (Milestone 2+) and the validator (Milestone 4+).
"""

from __future__ import annotations

from enum import Enum


class StitchType(Enum):
    """Atomic crochet stitch operations (US terms).

    SC  — single crochet: works into 1 existing stitch, makes 1 new stitch.
    INC — increase (2 sc in the same stitch): works into 1, makes 2.
    DEC — decrease (2 sc together): works into 2, makes 1.
    """

    SC = "sc"
    INC = "inc"
    DEC = "dec"

    @property
    def consumes_per_unit(self) -> int:
        """Number of existing stitches one instance of this stitch works into."""
        if self is StitchType.DEC:
            return 2
        return 1

    @property
    def produces_per_unit(self) -> int:
        """Number of new stitches one instance of this stitch adds."""
        if self is StitchType.INC:
            return 2
        if self is StitchType.DEC:
            return 1
        return 1
