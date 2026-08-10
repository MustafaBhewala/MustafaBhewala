from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta
from pathlib import Path


PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]


def parse_payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def level_for_count(count: int, max_count: int) -> int:
    if count <= 0:
        return 0
    if max_count <= 0:
        return 1
    return min(5, max(1, math.ceil(count / max_count * 5)))


def build_grid(days: list[dict[str, object]]) -> list[dict[str, object]]:
    day_map = {
        datetime.strptime(str(day["date"]), "%Y-%m-%d").date(): int(day["count"])
        for day in days
    }
    latest = max(day_map)
    sunday_offset = (latest.weekday() + 1) % 7
    latest_sunday = latest - timedelta(days=sunday_offset)
    start = latest_sunday - timedelta(weeks=52)
    max_count = max(day_map.values(), default=0)

    cells: list[dict[str, object]] = []
    for week in range(53):
        for day_index in range(7):
            current = start + timedelta(days=week * 7 + day_index)
            count = day_map.get(current, 0)
            cells.append(
                {
                    "date": current.isoformat(),
                    "count": count,
                    "level": level_for_count(count, max_count),
                    "week": week,
                    "day": day_index,
                }
            )
    return cells


def build_svg(payload: dict[str, object]) -> str:
    days = list(payload["days"])
    cells = build_grid(days)
    total = int(payload["total"])

    cell_size = 11
    gap = 3
    grid_width = 53 * (cell_size + gap) - gap
    grid_height = 7 * (cell_size + gap) - gap
    width = 850
    height = 230

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        "<style>",
        "  .panel { fill: #0d1117; }",
        "  .title { fill: #c9d1d9; font: 700 16px ui-monospace, SFMono-Regular, Consolas, Menlo, monospace; }",
        "  .subtle { fill: #8b949e; font: 12px ui-monospace, SFMono-Regular, Consolas, Menlo, monospace; }",
        "  .footer { fill: #d0d7de; font: 13px ui-monospace, SFMono-Regular, Consolas, Menlo, monospace; }",
        "  .cell { opacity: 0; transform: translateY(-5px); transform-box: fill-box; transform-origin: center; animation: reveal 0.44s ease forwards; }",
        "  @keyframes reveal { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }",
        "</style>",
        '<rect class="panel" x="0" y="0" width="850" height="230" rx="18" />',
        '<text x="24" y="28" class="title">contributions</text>',
        '<text x="24" y="48" class="subtle">Less</text>',
        f'<text x="790" y="48" class="subtle">More</text>',
    ]

    legend_x = 46
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{legend_x + index * 18}" y="38" width="12" height="12" rx="3" fill="{color}" />')

    parts.append(f'<text x="24" y="209" class="footer">{total:,} contributions in the last year</text>')

    for cell in cells:
        x = 24 + int(cell["week"]) * (cell_size + gap)
        y = 68 + int(cell["day"]) * (cell_size + gap)
        delay = int(cell["week"]) * 14 + int(cell["day"]) * 16
        parts.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="3" fill="{PALETTE[int(cell["level"])]}" style="animation-delay:{delay}ms" />'
        )

    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the contribution heatmap SVG.")
    parser.add_argument("--input", type=Path, default=Path("data/contributions.json"), help="Input JSON path")
    parser.add_argument("--output", type=Path, default=Path("contrib-heatmap.svg"), help="Output SVG path")
    args = parser.parse_args()

    payload = parse_payload(args.input)
    args.output.write_text(build_svg(payload), encoding="utf-8")


if __name__ == "__main__":
    main()