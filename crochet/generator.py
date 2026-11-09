"""Crochet pattern generator (Milestone 3: flat circle only).

Translates geometry results into structured domain Pattern objects. This
module contains ZERO arithmetic: round counts and stitch counts come from
crochet.geometry, and instruction semantics come from the domain StitchType
enum. The generator's expected_start_count / expected_end_count values are
CLAIMS taken from geometry — the validator (Milestone 4) will recompute
them independently from the raw instructions.

Crochet knowledge lives in this package only; nothing else imports from it.
"""

from __future__ import annotations

from patternforge.crochet.geometry import rounds_for_circle, stitches_for_circle_round
from patternforge.domain.pattern import Gauge, Pattern, PatternRound, StitchInstruction
from patternforge.domain.shapes import ShapeDimensions, ShapeType
from patternforge.domain.stitches import StitchType


def _round_1() -> PatternRound:
    """Magic ring round: 6 sc worked into the ring (consumes 0 stitches)."""
    return PatternRound(
        number=1,
        is_start_ring=True,
        instructions=[StitchInstruction(StitchType.SC, count=6)],
        expected_start_count=0,
        expected_end_count=stitches_for_circle_round(1),
        note="6 sc in magic ring",
    )


def _increase_round(number: int) -> PatternRound:
    """One circle round r >= 2: '[inc, sc x (r-2)] x 6'.

    Each of the 6 repeats consumes 1 (inc) + (r-2) (sc) = r-1 stitches, so
    the round consumes exactly the previous round's 6(r-1) stitches and
    produces 6(r+1-1) = 6r stitches.
    """
    if number < 2:
        raise ValueError("increase rounds start at round 2")

    instructions = [StitchInstruction(StitchType.INC, count=1, repeat=6)]
    sc_between = number - 2
    if sc_between > 0:
        # Round 2 has no plain sc between increases; rounds 3+ do.
        instructions.append(StitchInstruction(StitchType.SC, count=sc_between, repeat=6))

    return PatternRound(
        number=number,
        is_start_ring=False,
        instructions=instructions,
        expected_start_count=stitches_for_circle_round(number - 1),
        expected_end_count=stitches_for_circle_round(number),
        note="6 increases evenly spaced",
    )


def generate_circle(diameter_cm: float, gauge: Gauge) -> Pattern:
    """Generate a structured pattern for a flat single-crochet circle.

    The number of rounds and all stitch counts come from crochet.geometry.
    Raises ValueError for diameter_cm <= 0 (propagated from geometry).
    """
    total_rounds = rounds_for_circle(diameter_cm, gauge)

    rounds = [_round_1()]
    rounds.extend(_increase_round(r) for r in range(2, total_rounds + 1))

    return Pattern(
        shape=ShapeType.CIRCLE,
        gauge=gauge,
        dimensions=ShapeDimensions(diameter_cm=diameter_cm),
        rounds=rounds,
        convention="US",
    )
