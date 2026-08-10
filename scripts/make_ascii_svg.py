from __future__ import annotations

import argparse
import base64
from xml.etree import ElementTree
from pathlib import Path

from PIL import Image


RAMP = " .`:-=+*cs#%@"
GAMMA = 1.7


def build_svg_wrapper(svg_path: Path) -> str:
    source_text = svg_path.read_text(encoding="utf-8")
    root = ElementTree.fromstring(source_text)
    view_box = root.attrib.get("viewBox", "0 0 600 600")
    width = root.attrib.get("width", "600")
    height = root.attrib.get("height", "600")
    view_box_values = view_box.split()
    numeric_width = view_box_values[2] if len(view_box_values) >= 3 else "600"
    numeric_height = view_box_values[3] if len(view_box_values) >= 4 else "600"
    encoded = base64.b64encode(source_text.encode("utf-8")).decode("ascii")
    href = f"data:image/svg+xml;base64,{encoded}"

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_box}" width="{width}" height="{height}">'
        f'<defs>'
        f'<mask id="reveal" maskUnits="userSpaceOnUse" x="0" y="0" width="{numeric_width}" height="{numeric_height}">'
        f'<rect x="0" y="0" width="0" height="{numeric_height}" fill="white">'
        f'<animate attributeName="width" from="0" to="{numeric_width}" begin="0s" dur="1.8s" fill="freeze" />'
        f'</rect>'
        f'</mask>'
        f'</defs>'
        f'<rect x="0" y="0" width="100%" height="100%" fill="#0d1117" />'
        f'<image href="{href}" x="0" y="0" width="{numeric_width}" height="{numeric_height}" preserveAspectRatio="xMidYMid meet" mask="url(#reveal)" style="filter: brightness(0) invert(1);">'
        f'<animate attributeName="opacity" values="0;1" begin="0s" dur="0.25s" fill="freeze" />'
        f'</image>'
        f'</svg>'
    )


def brightness_to_glyph(value: int) -> str:
    scale = len(RAMP) - 1
    normalized = (value / 255) ** GAMMA
    index = round((1 - normalized) * scale)
    return RAMP[max(0, min(scale, index))]


def load_cells(image_path: Path, width: int) -> list[str]:
    if image_path.suffix.lower() == ".svg":
        raise ValueError("SVG input is handled by build_svg_wrapper and should not reach raster loading.")

    image = Image.open(image_path).convert("L")
    aspect_ratio = image.height / image.width
    height = max(1, round(width * aspect_ratio * 0.49))
    resized = image.resize((width, height), Image.Resampling.LANCZOS)

    rows: list[str] = []
    for y in range(height):
        rows.append("".join(brightness_to_glyph(resized.getpixel((x, y))) for x in range(width)))
    return rows


def build_svg(rows: list[str], font_size: int = 11) -> str:
    width = len(rows[0])
    height = len(rows)
    char_width = 6.6
    char_height = 13.0
    svg_width = int(width * char_width)
    svg_height = int(height * char_height)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">',
        "<defs>",
    ]

    for index in range(height):
        begin = f"{index * 0.045:.3f}s"
        parts.append(
            f'<clipPath id="row-{index}" clipPathUnits="userSpaceOnUse">'
            f'<rect x="0" y="{index * char_height:.2f}" width="0" height="{char_height:.2f}">'
            f'<animate attributeName="width" from="0" to="{svg_width}" begin="{begin}" dur="0.75s" fill="freeze" />'
            f"</rect></clipPath>"
        )

    parts.append("</defs>")
    parts.append(
        f'<style>text{{font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace;font-size:{font_size}px;fill:#d7d7d7;letter-spacing:0;}}</style>'
    )

    for index, row in enumerate(rows):
        y = index * char_height
        begin = f"{index * 0.045:.3f}s"
        cursor_width = 4
        parts.append(f'<g clip-path="url(#row-{index})">')
        parts.append(f'<text x="0" y="{y:.2f}" xml:space="preserve">{row}</text>')
        parts.append(
            f'<rect x="0" y="{y + 1:.2f}" width="{cursor_width}" height="{font_size + 1}" fill="#d7d7d7">'
            f'<animate attributeName="x" from="0" to="{max(0, svg_width - cursor_width)}" begin="{begin}" dur="0.75s" fill="freeze" />'
            f"</rect>"
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a prepped portrait into an ASCII SVG.")
    parser.add_argument("--input", type=Path, default=Path("source-prepped.png"), help="Input prepped image")
    parser.add_argument("--output", type=Path, default=Path("avi-ascii.svg"), help="Output SVG path")
    parser.add_argument("--width", type=int, default=88, help="Character grid width")
    args = parser.parse_args()

    if args.input.suffix.lower() == ".svg":
        args.output.write_text(build_svg_wrapper(args.input), encoding="utf-8")
        return

    rows = load_cells(args.input, args.width)
    args.output.write_text(build_svg(rows), encoding="utf-8")


if __name__ == "__main__":
    main()