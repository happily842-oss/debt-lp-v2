#!/usr/bin/env python3
"""Generate 4:3 black background image with white brush-style Japanese text."""

import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TEXT_LINES = [
    "色んな方々にかわいがっていただき",
    "今日も生きれてます",
    "マジで感謝です",
]

WIDTH = 2400
HEIGHT = 1800
BG = (0, 0, 0)
FG = (255, 255, 255)
FONT_URL = (
    "https://github.com/google/fonts/raw/main/ofl/yujisyuku/YujiSyuku-Regular.ttf"
)
CACHE_DIR = Path.home() / ".cache" / "brush_message_gen"
OUT_JPEG = Path(__file__).resolve().parent.parent / "brush_message_4x3.jpg"
OUT_PNG = Path(__file__).resolve().parent.parent / "brush_message_4x3.png"


def _font_path() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / "YujiSyuku-Regular.ttf"
    if not path.exists():
        urllib.request.urlretrieve(FONT_URL, path)
    return path


def main() -> None:
    font_path = _font_path()
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    margin_x = int(WIDTH * 0.08)
    max_text_width = WIDTH - 2 * margin_x
    font_size = 120
    font = ImageFont.truetype(str(font_path), font_size)

    while font_size > 40:
        font = ImageFont.truetype(str(font_path), font_size)
        line_widths = [
            draw.textbbox((0, 0), line, font=font)[2]
            - draw.textbbox((0, 0), line, font=font)[0]
            for line in TEXT_LINES
        ]
        if max(line_widths) <= max_text_width:
            break
        font_size -= 4

    line_heights = []
    for line in TEXT_LINES:
        bb = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bb[3] - bb[1])
    line_gap = int(max(line_heights) * 0.25)
    total_h = sum(line_heights) + line_gap * (len(TEXT_LINES) - 1)
    y0 = (HEIGHT - total_h) // 2

    y = y0
    for i, line in enumerate(TEXT_LINES):
        bb = draw.textbbox((0, 0), line, font=font)
        w = bb[2] - bb[0]
        x = (WIDTH - w) // 2
        draw.text((x, y), line, font=font, fill=FG)
        y += line_heights[i] + (line_gap if i < len(TEXT_LINES) - 1 else 0)

    img.save(OUT_JPEG, "JPEG", quality=95, optimize=True)
    img.save(OUT_PNG, "PNG", optimize=True)
    print(f"Wrote {OUT_JPEG} and {OUT_PNG}")


if __name__ == "__main__":
    main()
