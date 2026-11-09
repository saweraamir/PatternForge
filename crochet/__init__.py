"""Crochet-specific production method (reserved — Milestone 2+).

Will contain:
    geometry.py  — pure math: rounds needed, per-round stitch counts.
    generator.py — builds domain Pattern objects from geometry results.

Nothing else may import from this package; crochet logic stays isolated here
so future production methods (e.g. knitting) live in sibling packages.
"""
