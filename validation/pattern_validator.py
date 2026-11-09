"""Milestone 4 — Pattern Validator (V1–V7).

APPROVED SPECIFICATION — PERSISTED AT DESIGN REVIEW.

The exact V1–V7 numbering below was NOT previously recorded in this
repository: earlier modules (domain/pattern.py, crochet/generator.py, and
this package's former placeholder docstring) described validator
*responsibilities* in prose only, and the numbered specification existed
solely in design discussion. This docstring is now the canonical, approved
specification. Approved with these conditions:

1. This block documents its own provenance (newly approved spec).
2. V2 verifies start-ring consumption from RAW StitchInstruction values,
   never via PatternRound.total_consumed, which short-circuits to 0 for
   any round with is_start_ring=True regardless of its instructions.
3. V6 uses a validator-side constant (CIRCLE_GROWTH_PER_ROUND) instead of
   importing crochet.geometry. The duplication is intentional: validation
   stays independent of the crochet package so it can validate hand-built
   patterns and future techniques. A dedicated drift-guard test asserts
   equality with geometry.STITCHES_PER_INCREASE_ROUND so the two can never
   silently diverge.
4. validate_pattern() returns every ValidationError in deterministic
   V1→V7 order, never raises on validation failures, never mutates the
   input pattern, and performs no I/O.

Rules (all read-only; counts are recomputed from raw instructions):

V1 Structure — the rounds list is non-empty; round numbers are strictly
   sequential starting at 1; every round has at least one instruction.
V2 Start ring — exactly one round has is_start_ring=True; it is round 1;
   and every one of its raw instructions is a plain placement worked into
   the magic ring: consumes_per_unit == 1 and produces_per_unit == 1.
   (INC/DEC reference stitches that do not exist yet; note that a VALID
   ring's raw consumption is nonzero — the sc stitches work into the ring
   itself — so "consumption == 0" would be wrong in both directions.
   PatternRound.total_consumed short-circuits to 0 for start rings and is
   therefore never consulted.)
V3 Continuity — for every round after the first, its raw consumption
   equals the previous round's recomputed production.
V4 Claim agreement — each round's expected_start_count equals 0 for a
   start ring or the previous round's recomputed production otherwise;
   expected_end_count equals the round's own recomputed production.
   The generator's claims are never trusted blindly.
V5 Dimensions — pattern.dimensions carries every field required by
   pattern.shape (ShapeDimensions.missing_fields).
V6 Circle growth — for CIRCLE patterns only: the n-th round produces
   exactly CIRCLE_GROWTH_PER_ROUND * n stitches, and every round after
   the first contains at least one increase.
V7 Convention — pattern.convention is "US", the only convention the
   stitch vocabulary defines.
"""

from __future__ import annotations

from dataclasses import dataclass

from patternforge.domain.pattern import Pattern, PatternRound
from patternforge.domain.shapes import ShapeType
from patternforge.domain.stitches import StitchType

#: Canonical sc circle growth: 6 evenly-spaced increases per round.
#:
#: INTENTIONAL DUPLICATION of crochet.geometry.STITCHES_PER_INCREASE_ROUND.
#: The validator must not import from the crochet package (it validates
#: hand-built patterns and future techniques, so validation depends on the
#: domain only). A drift-guard test asserts the two constants stay equal;
#: if geometry ever changes, that test fails loudly instead of the
#: validator silently disagreeing with the generator.
CIRCLE_GROWTH_PER_ROUND = 6

#: The only stitch convention the domain vocabulary defines.
SUPPORTED_CONVENTION = "US"


@dataclass(frozen=True)
class ValidationError:
    """One failed rule: which rule, why, and (if relevant) which round."""

    rule: str
    message: str
    round_number: int | None = None


def _raw_consumed(round_: PatternRound) -> int:
    """Consumption recomputed from the RAW instructions of a round.

    Deliberately avoids PatternRound.total_consumed, which returns 0 for
    ANY round flagged is_start_ring=True, even if its instructions would
    consume stitches. V2 must catch such malformed start rings.
    """
    return sum(i.total_consumed for i in round_.instructions)


def _check_v1_structure(pattern: Pattern) -> list[ValidationError]:
    errors: list[ValidationError] = []
    if not pattern.rounds:
        return [ValidationError("V1", "pattern has no rounds")]
    expected_numbers = range(1, len(pattern.rounds) + 1)
    for round_, expected in zip(pattern.rounds, expected_numbers):
        if round_.number != expected:
            errors.append(
                ValidationError(
                    "V1",
                    f"round numbers must be sequential 1..{len(pattern.rounds)}; "
                    f"found round {round_.number} at position {expected}",
                    round_number=round_.number,
                )
            )
        if not round_.instructions:
            errors.append(
                ValidationError(
                    "V1",
                    f"round {round_.number} has no instructions",
                    round_number=round_.number,
                )
            )
    return errors


def _check_v2_start_ring(pattern: Pattern) -> list[ValidationError]:
    errors: list[ValidationError] = []
    start_rings = [r for r in pattern.rounds if r.is_start_ring]
    if len(start_rings) != 1:
        errors.append(
            ValidationError(
                "V2",
                f"pattern must have exactly one start ring; found {len(start_rings)}",
            )
        )
        return errors
    ring = start_rings[0]
    if ring.number != 1:
        errors.append(
            ValidationError(
                "V2",
                f"the start ring must be round 1; found round {ring.number}",
                round_number=ring.number,
            )
        )
    # RAW recount from StitchInstruction values — never
    # PatternRound.total_consumed, which short-circuits to 0 for any start
    # ring. A valid ring works plain stitches INTO the magic ring, so each
    # raw instruction unit must consume exactly 1 (the ring) and produce
    # exactly 1. INC/DEC reference existing stitches that do not exist yet.
    bad = [
        i
        for i in ring.instructions
        if i.stitch_type.consumes_per_unit != 1 or i.stitch_type.produces_per_unit != 1
    ]
    if bad:
        found = ", ".join(sorted({i.stitch_type.value for i in bad}))
        errors.append(
            ValidationError(
                "V2",
                "the start ring works into the magic ring, so every raw "
                "instruction must be a plain stitch placement; found " + found,
                round_number=ring.number,
            )
        )
    return errors

def _check_v3_continuity(pattern: Pattern) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for previous, current in zip(pattern.rounds, pattern.rounds[1:]):
        produced = previous.total_produced
        consumed = _raw_consumed(current)
        if consumed != produced:
            errors.append(
                ValidationError(
                    "V3",
                    f"round {current.number} consumes {consumed} stitches but "
                    f"round {previous.number} produces {produced}",
                    round_number=current.number,
                )
            )
    return errors


def _check_v4_claims(pattern: Pattern) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for index, round_ in enumerate(pattern.rounds):
        if round_.is_start_ring:
            claimed_start: int | None = 0
        elif index == 0:
            # A non-start round as the first round has no previous round to
            # derive a claim from; the missing start ring is reported by V2.
            claimed_start = None
        else:
            claimed_start = pattern.rounds[index - 1].total_produced
        if claimed_start is not None and round_.expected_start_count != claimed_start:
            errors.append(
                ValidationError(
                    "V4",
                    f"round {round_.number} claims expected_start_count="
                    f"{round_.expected_start_count} but recomputation gives "
                    f"{claimed_start}",
                    round_number=round_.number,
                )
            )
        produced = round_.total_produced
        if round_.expected_end_count != produced:
            errors.append(
                ValidationError(
                    "V4",
                    f"round {round_.number} claims expected_end_count="
                    f"{round_.expected_end_count} but its instructions "
                    f"produce {produced}",
                    round_number=round_.number,
                )
            )
    return errors


def _check_v5_dimensions(pattern: Pattern) -> list[ValidationError]:
    missing = pattern.dimensions.missing_fields(pattern.shape)
    if missing:
        return [
            ValidationError(
                "V5",
                f"{pattern.shape.value} pattern is missing required "
                f"dimensions: {', '.join(missing)}",
            )
        ]
    return []


def _check_v6_circle_growth(pattern: Pattern) -> list[ValidationError]:
    if pattern.shape is not ShapeType.CIRCLE:
        return []
    errors: list[ValidationError] = []
    for index, round_ in enumerate(pattern.rounds):
        position = index + 1  # positional; broken numbering is reported by V1
        expected = CIRCLE_GROWTH_PER_ROUND * position
        produced = round_.total_produced
        if produced != expected:
            errors.append(
                ValidationError(
                    "V6",
                    f"circle round {round_.number} must produce {expected} "
                    f"stitches (canonical growth of {CIRCLE_GROWTH_PER_ROUND} "
                    f"per round); it produces {produced}",
                    round_number=round_.number,
                )
            )
        if position >= 2 and not any(
            i.stitch_type is StitchType.INC for i in round_.instructions
        ):
            errors.append(
                ValidationError(
                    "V6",
                    f"circle round {round_.number} contains no increase; the "
                    f"canonical circle adds {CIRCLE_GROWTH_PER_ROUND} evenly "
                    "spaced increases every round",
                    round_number=round_.number,
                )
            )
    return errors


def _check_v7_convention(pattern: Pattern) -> list[ValidationError]:
    if pattern.convention != SUPPORTED_CONVENTION:
        return [
            ValidationError(
                "V7",
                f"unsupported convention {pattern.convention!r}; only "
                f"{SUPPORTED_CONVENTION!r} is defined by the stitch vocabulary",
            )
        ]
    return []


def validate_pattern(pattern: Pattern) -> list[ValidationError]:
    """Validate a pattern against rules V1–V7.

    Returns every detected error in deterministic V1→V7 order (an empty
    list means the pattern is valid). Never raises on validation failures,
    never mutates the input pattern, and performs no I/O.
    """
    checks = (
        _check_v1_structure,
        _check_v2_start_ring,
        _check_v3_continuity,
        _check_v4_claims,
        _check_v5_dimensions,
        _check_v6_circle_growth,
        _check_v7_convention,
    )
    errors: list[ValidationError] = []
    for check in checks:
        errors.extend(check(pattern))
    return errors
