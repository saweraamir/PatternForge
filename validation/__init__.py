"""Pattern consistency validation (Milestone 4 — implemented).

The canonical, approved V1–V7 specification lives in the module docstring
of patternforge.validation.pattern_validator. It was first persisted at
design review; earlier repository modules described validator
responsibilities only in prose, without a numbered specification.

Exports: validate_pattern, ValidationError. The validator reads only the
domain models — it never imports from crochet/ or rendering/, never
mutates patterns, and does no I/O.
"""

from patternforge.validation.pattern_validator import (
    ValidationError,
    validate_pattern,
)

__all__ = ["ValidationError", "validate_pattern"]
