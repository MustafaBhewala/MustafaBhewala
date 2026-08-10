from __future__ import annotations

import argparse
import os
from pathlib import Path


ROWS = [
    ("Now", "Shipping profile art and automation"),
    ("Prev", "Building client systems, APIs, and workflows"),
    ("Stack", "React, Node.js, Python, OpenCV, GitHub Actions"),
    ("Highlights", "ERP, e-commerce, AI tools, and CI/CD"),
]


def build_svg(static: bool) -> str:
    width = 490
    height = 285
    row_y = [110, 153, 196, 239]
    lines = []

    styles = [
        "<style>",
        "  .panel { fill: #0d1117; stroke: #30363d; stroke-width: 1.2; }",
        "  .titlebar { fill: #161b22; }",
        "  .chrome { fill: #8b949e; font-family: ui-monospace, SFMono-Regular, Consolas, Menlo, monospace; }",
        "  .label { fill: #58a6ff; font-weight: 700; }",
        "  .value { fill: #d0d7de; }",
    ]
    if not static:
        styles.extend(
            [
                "  .line { opacity: 0; transform: translateX(16px); animation: lineIn 0.58s ease forwards; transform-box: fill-box; transform-origin: left center; }",
                "  .line-1 { animation-delay: 0.15s; }",
                "  .line-2 { animation-delay: 0.28s; }",
                "  .line-3 { animation-delay: 0.41s; }",
                "  .line-4 { animation-delay: 0.54s; }",
                "  @keyframes lineIn { from { opacity: 0; transform: translateX(16px); } to { opacity: 1; transform: translateX(0); } }",
            ]
        )
    else:
        styles.append("  .line { opacity: 1; transform: translateX(0); }")
    styles.append("</style>")

    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    lines.append("".join(styles))
    lines.append(
        f'<rect class="panel" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="18" />')
    lines.append(
        '<rect class="titlebar" x="0.5" y="0.5" width="489" height="38" rx="18" />')
    lines.append(
        '<rect class="titlebar" x="0.5" y="20" width="489" height="18" />')
    lines.append('<circle cx="24" cy="19" r="5" fill="#ff5f56" />')
    lines.append('<circle cx="42" cy="19" r="5" fill="#ffbd2e" />')
    lines.append('<circle cx="60" cy="19" r="5" fill="#27c93f" />')
    lines.append('<text x="20" y="72" class="chrome" font-size="18">neofetch</text>')
    lines.append('<text x="20" y="90" class="chrome" font-size="11">bhewala.mustafa.25@gmail.com</text>')

    for index, ((label, value), y) in enumerate(zip(ROWS, row_y), start=1):
        lines.append(f'<g class="line line-{index}">')
        lines.append(f'<text x="20" y="{y}" class="label" font-size="16">{label}</text>')
        lines.append(f'<text x="110" y="{y}" class="value" font-size="16">{value}</text>')
        lines.append('</g>')

    lines.append('</svg>')
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the profile info card SVG.")
    parser.add_argument("--output", type=Path,
                        default=Path("info-card.svg"), help="Output SVG path")
    args = parser.parse_args()

    static = os.environ.get("STATIC") == "1"
    args.output.write_text(build_svg(static=static), encoding="utf-8")


if __name__ == "__main__":
    main()
