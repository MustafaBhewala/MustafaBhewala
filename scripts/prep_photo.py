from __future__ import annotations

import argparse
import io
from base64 import b64decode
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from rembg import remove

try:
    import cairosvg
except ImportError:  # pragma: no cover - helpful local error path
    cairosvg = None


def load_source_image(input_path: Path) -> Image.Image:
    if input_path.suffix.lower() == ".svg":
        if cairosvg is None:
            raise RuntimeError("SVG input requires cairosvg. Install the portrait-only dependencies first.")

        svg_bytes = input_path.read_bytes()
        png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=2200)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    return Image.open(input_path).convert("RGBA")


def prep_photo(input_path: Path, output_path: Path) -> None:
    source = load_source_image(input_path)
    source = ImageOps.exif_transpose(source).convert("RGBA")

    buffer = io.BytesIO()
    source.save(buffer, format="PNG")
    stripped = Image.open(io.BytesIO(remove(buffer.getvalue()))).convert("RGBA")

    rgba = np.array(stripped)
    rgb = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2LAB)
    luminance, a_channel, b_channel = cv2.split(rgb)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    boosted = clahe.apply(luminance)
    enhanced = cv2.merge((boosted, a_channel, b_channel))
    enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    foreground = Image.fromarray(enhanced_rgb, mode="RGB")
    alpha = Image.fromarray(rgba[:, :, 3], mode="L")
    white = Image.new("RGB", foreground.size, "white")
    white.paste(foreground, mask=alpha)

    mask = alpha.point(lambda value: 255 if value > 10 else 0)
    bbox = mask.getbbox()
    if bbox is not None:
        left, top, right, bottom = bbox
        pad_x = int((right - left) * 0.10)
        pad_y = int((bottom - top) * 0.12)
        left = max(0, left - pad_x)
        top = max(0, top - pad_y)
        right = min(white.width, right + pad_x)
        bottom = min(white.height, bottom + pad_y)
        white = white.crop((left, top, right, bottom))

    grayscale = ImageOps.grayscale(white)
    grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
    grayscale = ImageEnhance.Contrast(grayscale).enhance(1.9)
    grayscale = ImageEnhance.Sharpness(grayscale).enhance(1.25)
    grayscale.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a portrait for ASCII conversion.")
    parser.add_argument("input", type=Path, help="Input photo path")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("source-prepped.png"),
        help="Output image path (default: source-prepped.png)",
    )
    args = parser.parse_args()

    prep_photo(args.input, args.output)


if __name__ == "__main__":
    main()