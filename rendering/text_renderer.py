"""Rendering of patterns for humans and machines.

Converts a domain Pattern into human-readable text and JSON. Contains no
computation — it only formats what the models and generator already know.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from enum import Enum

from patternforge.domain.pattern import Pattern, PatternRound, StitchInstruction
from patternforge.domain.stitches import StitchType


def _stitch_part(instruction: StitchInstruction) -> str:
    """One stitch group, e.g. '6 sc', 'inc', or '[inc] x 6'."""
    name = instruction.stitch_type.value
    if instruction.repeat > 1:
        part = name if instruction.count == 1 else f"{instruction.count} {name}"
        return f"[{part}] x {instruction.repeat}"
    if instruction.count == 1:
        return name
    return f"{instruction.count} {name}"


def render_round(round_: PatternRound) -> str:
    """One readable line, e.g. 'R1: 6 sc in magic ring (0 -> 6)'."""
    parts = ", ".join(_stitch_part(i) for i in round_.instructions)
    line = f"R{round_.number}: {parts}"
    if round_.is_start_ring:
        line += " in magic ring"
    return f"{line}  ({round_.expected_start_count} -> {round_.expected_end_count})"


def render_pattern(pattern: Pattern) -> str:
    """Full human-readable pattern text (round-by-round)."""
    lines = [
        f"PatternForge — {pattern.shape.value.title()} "
        f"(US terms, right-handed, spiral)",
        f"Target diameter: {pattern.dimensions.diameter_cm} cm",
        f"Gauge: {pattern.gauge.stitches_per_cm} sc/cm, "
        f"{pattern.gauge.rounds_per_cm} rounds/cm",
        "",
    ]
    lines.extend(render_round(r) for r in pattern.rounds)
    lines += [
        "",
        "Note: stitch counts are simplified estimates for a canonical,",
        "tension-free fabric. Gauge and hand tension determine the real size",
        "of the finished item.",
    ]
    return "\n".join(lines)


def _json_default(obj: object) -> object:
    """dataclasses.asdict keeps Enum members as-is; convert them to values."""
    if isinstance(obj, Enum):
        return obj.value
    return str(obj)


def to_json(pattern: Pattern) -> str:
    """Serialize the pattern to JSON via dataclasses.asdict."""
    return json.dumps(asdict(pattern), indent=2, default=_json_default)
