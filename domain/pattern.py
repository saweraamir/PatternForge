"""Core domain models: Gauge, StitchInstruction, PatternRound, Pattern.

Stitch-count semantics:
- A StitchInstruction says an operation is worked `count` times, `repeat` times.
- total_consumed = count * repeat * StitchType.consumes_per_unit
- total_produced = count * repeat * StitchType.produces_per_unit
- Round 1 (start ring) consumes 0 stitches (worked into the magic ring).
- Rounds 2+ must consume exactly as many stitches as the previous round produced
  (checked later by the validator, not here).

This module intentionally contains no geometry math and no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .shapes import ShapeDimensions, ShapeType
from .stitches import StitchType


@dataclass(frozen=True)
class Gauge:
    """Stitch density of the crocheter's fabric.

    stitches_per_cm: single-crochet stitches per centimeter.
    rounds_per_cm:   crochet rounds per centimeter (fabric height per round).
    """

    stitches_per_cm: float
    rounds_per_cm: float
    hook_mm: str | None = None
    yarn: str | None = None

    def __post_init__(self) -> None:
        if self.stitches_per_cm <= 0:
            raise ValueError("stitches_per_cm must be positive")
        if self.rounds_per_cm <= 0:
            raise ValueError("rounds_per_cm must be positive")


@dataclass(frozen=True)
class StitchInstruction:
    """One stitch operation, worked `count` times, repeated `repeat` times.

    A repeated sequence such as "[inc, sc] x 6" is represented flatly as two
    instructions: StitchInstruction(INC, 1, repeat=6) and
    StitchInstruction(SC, 1, repeat=6). No nesting — keeps recounting trivial.
    """

    stitch_type: StitchType
    count: int
    repeat: int = 1

    def __post_init__(self) -> None:
        if self.count < 1:
            raise ValueError("count must be at least 1")
        if self.repeat < 1:
            raise ValueError("repeat must be at least 1")

    @property
    def total_consumed(self) -> int:
        """Existing stitches this instruction works into."""
        return self.count * self.repeat * self.stitch_type.consumes_per_unit

    @property
    def total_produced(self) -> int:
        """New stitches this instruction adds to the round."""
        return self.count * self.repeat * self.stitch_type.produces_per_unit


@dataclass
class PatternRound:
    """One round of a pattern.

    expected_start_count / expected_end_count are the GENERATOR's claims about
    how many stitches are available before / after the round. The validator
    (Milestone 4) recomputes both from the instructions and compares — the
    generator is never trusted blindly.
    """

    number: int
    is_start_ring: bool
    instructions: list[StitchInstruction] = field(default_factory=list)
    expected_start_count: int = 0
    expected_end_count: int = 0
    note: str = ""

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("round number must be at least 1")
        if self.expected_start_count < 0:
            raise ValueError("expected_start_count must be non-negative")
        if self.expected_end_count < 0:
            raise ValueError("expected_end_count must be non-negative")

    @property
    def total_consumed(self) -> int:
        """Existing stitches worked into this round (0 for the start ring)."""
        if self.is_start_ring:
            return 0
        return sum(i.total_consumed for i in self.instructions)

    @property
    def total_produced(self) -> int:
        """New stitches this round adds."""
        return sum(i.total_produced for i in self.instructions)


@dataclass
class Pattern:
    """A complete structured pattern for one shape.

    rounds is an ordered list; the validator later checks continuity between
    rounds and shape-specific invariants. This class holds data only.
    """

    shape: ShapeType
    gauge: Gauge
    dimensions: ShapeDimensions
    rounds: list[PatternRound]
    convention: str = "US"
