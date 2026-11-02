#!/usr/bin/env python3
"""Roll a regular pentagon over all five edges, recursively.

Each generation takes the pentagonal outline of the previous generation
and reflects its entire interior pattern over each of the five sides.
The original stays in place, producing six copies at every iteration.

SVG output requires only Python's standard library; for PNG, install
CairoSVG (on Debian: python3-cairosvg).

Examples:
    python3 pentagon_roll.py 1
    python3 pentagon_roll.py 7 -o snowflake.svg
    python3 pentagon_roll.py 4 --frames
    python3 pentagon_roll.py 5 --png --size 1400
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

PHI = (1.0 + math.sqrt(5.0)) / 2.0
SCALE = PHI ** 2
Point = tuple[float, float]


def regular_pentagon() -> list[Point]:
    """Regular pentagon with side length one, initially pointing upward."""
    radius = 1.0 / (2.0 * math.sin(math.pi / 5.0))
    return [
        (
            radius * math.cos(-math.pi / 2 + k * 2 * math.pi / 5),
            radius * math.sin(-math.pi / 2 + k * 2 * math.pi / 5),
        )
        for k in range(5)
    ]


def reflection_matrix(a: Point, b: Point) -> tuple[float, ...]:
    """Return SVG affine coefficients reflecting over the line through a, b.

    SVG matrix(A B C D E F) maps (x,y) to (A*x+C*y+E, B*x+D*y+F).
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    A = 2 * ux * ux - 1
    B = 2 * ux * uy
    C = B
    D = 2 * uy * uy - 1
    E = a[0] - A * a[0] - C * a[1]
    F = a[1] - B * a[0] - D * a[1]
    return A, B, C, D, E, F


def points_attr(poly: list[Point]) -> str:
    return " ".join(f"{x:.12g},{y:.12g}" for x, y in poly)


def render_svg(n: int, size: int = 1100) -> str:
    """Build compact recursive SVG without expanding 6**n polygons."""
    if n < 0:
        raise ValueError("generation must be nonnegative")
    if size < 100:
        raise ValueError("size must be at least 100")

    base = regular_pentagon()
    outline = base[:]
    defs = [
        f'<polygon id="cell" points="{points_attr(base)}"/>',
        '<g id="generation0"><use href="#cell"/></g>',
    ]

    for generation in range(1, n + 1):
        parts = [
            f'<g id="generation{generation}">',
            f'<use href="#generation{generation - 1}"/>',
        ]
        for side in range(5):
            a, b = outline[side], outline[(side + 1) % 5]
            matrix = " ".join(f"{x:.13g}" for x in reflection_matrix(a, b))
            parts.append(
                f'<use href="#generation{generation - 1}" '
                f'transform="matrix({matrix})"/>'
            )
        parts.append("</g>")
        defs.extend(parts)

        # The new outer pentagon is scaled by phi^2 and rotated 180 degrees.
        outline = [(-SCALE * x, -SCALE * y) for x, y in outline]

    xs, ys = zip(*outline)
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    side = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.10
    x0, y0 = cx - side / 2, cy - side / 2
    stroke_width = side * 1.1 / size

    return "\n".join([
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{x0:.13g} {y0:.13g} {side:.13g} {side:.13g}">',
        f'<title>Pentagon snowflake — generation {n}</title>',
        f'<desc>{6 ** n} unit pentagons; enclosing-pentagon scale '
        f'{SCALE ** n:.8g}; recursive edge reflections.</desc>',
        "<defs>", *defs, "</defs>",
        f'<rect x="{x0:.13g}" y="{y0:.13g}" width="{side:.13g}" '
        f'height="{side:.13g}" fill="#ffffff"/>',
        f'<polygon points="{points_attr(outline)}" fill="#cbdcdd"/>',
        f'<g fill="#fffdfa" stroke="#263840" '
        f'stroke-width="{stroke_width:.13g}" stroke-linejoin="round">',
        f'<use href="#generation{n}"/>',
        "</g>",
        f'<polygon points="{points_attr(outline)}" fill="none" '
        f'stroke="#263840" stroke-width="{stroke_width * 1.4:.13g}" '
        'stroke-linejoin="round"/>',
        "</svg>",
    ])


def save(svg: str, path: Path, png: bool, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"Created {path}")

    if png:
        try:
            import cairosvg
        except ImportError as exc:
            raise SystemExit(
                "PNG requires CairoSVG; SVG needs no extra dependencies."
            ) from exc
        png_path = path.with_suffix(".png")
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(png_path),
            output_width=size,
            output_height=size,
        )
        print(f"Created {png_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("N", nargs="?", type=int, default=2,
                        help="number of generations (default: 2)")
    parser.add_argument("-o", "--output", type=Path,
                        default=Path("pentagon_pattern.svg"),
                        help="output SVG file")
    parser.add_argument("--size", type=int, default=1100,
                        help="SVG/PNG size in pixels (default: 1100)")
    parser.add_argument("--png", action="store_true",
                        help="also export PNG using CairoSVG")
    parser.add_argument("--frames", action="store_true",
                        help="write every generation from 0 through N")
    args = parser.parse_args()

    if not 0 <= args.N <= 8:
        parser.error("N must be between 0 and 8")
    if args.size < 100:
        parser.error("--size must be at least 100")
    if args.output.suffix.lower() != ".svg":
        parser.error("output must have a .svg extension")

    for generation in (range(args.N + 1) if args.frames else [args.N]):
        path = (
            args.output.with_name(
                f"{args.output.stem}_N{generation}.svg"
            ) if args.frames else args.output
        )
        save(render_svg(generation, args.size), path, args.png, args.size)
        print(
            f"Generation {generation}: {6 ** generation:,} small pentagons; "
            f"scale {SCALE ** generation:.6f}x"
        )


if __name__ == "__main__":
    main()
