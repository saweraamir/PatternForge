"""PatternForge: structured, validated crochet pattern generation.

Package boundaries (dependencies point one way):
    cli -> app -> {crochet/generator, validation, rendering} -> domain
All modules communicate through the domain dataclasses only.
"""

__version__ = "0.1.0"
