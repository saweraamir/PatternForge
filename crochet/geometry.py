"""Pure geometry math for a flat single-crochet circle.

IMPORTANT — these are SIMPLIFIED ESTIMATES, not physically guaranteed
measurements. Real gauge varies with yarn, hook, and hand tension, and real
sc circles often ripple or cup. These functions compute mathematically
consistent numbers for a canonical, tension-free fabric only.

Model (US terms, spiral worked from a magic ring):
- Round 1: 6 sc in the magic ring; every round adds 6 evenly-spaced increases.
  Therefore the stitch count after round n is  S(n) = 6 * n.
- With `spc` stitches per cm, the circumference of round n is S(n) / spc, so
  its diameter is  d(n) = S(n) / (spc * pi).
- Rounds needed for a target diameter D:  n = ceil(D * pi * spc / 6), at
  least 1 round.

This module contains NO domain objects beyond reading Gauge, and NO I/O.
Crochet knowledge lives here; domain vocabulary lives in patternforge.domain.
"""

from __future__ import annotations

import math

from patternforge.domain.pattern import Gauge

#: Canonical sc circle growth: 6 evenly-spaced increases per round.
STITCHES_PER_INCREASE_ROUND = 6

#: Tight relative tolerance used ONLY to snap values that are within
#: floating-point error of an integer (real arithmetic error at these
#: magnitudes is ~1e-13 relative). The gap between legitimate round
#: boundaries is ~0.5, so this never changes a legitimate result.
_FP_SNAP_RELATIVE_TOLERANCE = 1e-9


def stitches_for_circle_round(n: int) -> int:
    """Stitch count after round n of the canonical circle: S(n) = 6 * n."""
    if n < 1:
        raise ValueError("round number must be at least 1")
    return STITCHES_PER_INCREASE_ROUND * n


def round_diameter_cm(n: int, gauge: Gauge) -> float:
    """Estimated diameter (cm) of the canonical circle after round n.

    Simplified estimate: d(n) = 6n / (pi * stitches_per_cm). Not a physically
    guaranteed measurement — actual size depends on gauge and tension.
    """
    if n < 1:
        raise ValueError("round number must be at least 1")
    return STITCHES_PER_INCREASE_ROUND * n / (math.pi * gauge.stitches_per_cm)


def rounds_for_circle(diameter_cm: float, gauge: Gauge) -> int:
    """Rounds needed to reach the target diameter (at least 1).

    Simplified estimate: n = ceil(D * pi * spc / 6). A target smaller than
    round 1 (d(1) = 6 / (pi * spc)) clamps to 1 round — the smallest
    crochetable circle — rather than raising an error.
    """
    if diameter_cm <= 0:
        raise ValueError("diameter_cm must be positive")

    x = diameter_cm * math.pi * gauge.stitches_per_cm / STITCHES_PER_INCREASE_ROUND

    # Snap to the nearest integer when within floating-point error, so a
    # diameter produced by round_diameter_cm() does not gain a spurious
    # extra round from ceil() on e.g. 11.000000000000002.
    nearest = round(x)
    if abs(x - nearest) <= _FP_SNAP_RELATIVE_TOLERANCE * max(1.0, abs(x)):
        x = float(nearest)

    return max(1, math.ceil(x))
