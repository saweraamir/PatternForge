"""Command-line interface (thin): parse args, generate, render, print.

Dependency direction: cli -> crochet/generator + rendering -> domain.
Invalid input prints a clear message to stderr and exits nonzero.
"""

from __future__ import annotations

import argparse
import sys

from patternforge.crochet.generator import generate_circle
from patternforge.domain.pattern import Gauge
from patternforge.rendering.text_renderer import render_pattern, to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patternforge",
        description=(
            "Generate structured crochet patterns. "
            "MVP supports the flat circle only (deterministic rules — "
            "no AI stitch identification from images)."
        ),
    )
    parser.add_argument(
        "--shape",
        choices=["circle"],
        default="circle",
        help="shape to generate (MVP supports 'circle' only)",
    )
    parser.add_argument(
        "--diameter", type=float, required=True, metavar="CM",
        help="target diameter in centimeters",
    )
    parser.add_argument(
        "--gauge", type=float, required=True, metavar="SC_PER_CM",
        help="stitch gauge: single crochets per centimeter",
    )
    parser.add_argument(
        "--rounds-per-cm", type=float, default=2.0, metavar="ROUNDS_PER_CM",
        help="round gauge: crochet rounds per centimeter (default: 2.0)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="output machine-readable JSON instead of text",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.diameter <= 0:
        print("Error: --diameter must be positive (centimeters).", file=sys.stderr)
        return 2
    if args.gauge <= 0 or args.rounds_per_cm <= 0:
        print("Error: --gauge and --rounds-per-cm must be positive.", file=sys.stderr)
        return 2

    try:
        gauge = Gauge(stitches_per_cm=args.gauge, rounds_per_cm=args.rounds_per_cm)
        pattern = generate_circle(args.diameter, gauge)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(to_json(pattern))
    else:
        print(render_pattern(pattern))
    return 0


if __name__ == "__main__":
    sys.exit(main())
