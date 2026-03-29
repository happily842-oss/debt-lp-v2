#!/usr/bin/env python3
"""Generate 4:3 black background image with white gyosho-style Japanese text."""

import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TEXT_LINES = [
    "色んな方々にかわいがっていただき",
    "今日も生きれてます",
    "マジで感謝です",
]

# 行書に近い流れる筆（Yuji Mai）
FONT_URL = (
    "https://github.com/google/fonts/raw/main/ofl/yujimai/YujiMai-Regular.ttf"
)
FONT_FILENAME = "YujiMai-Regular.ttf"

WIDTH = 2400
HEIGHT = 1800
BG = (0, 0, 0)
FG = (255, 255, 255)

# 画面いっぱい（最小限の余白）
MARGIN_X_RATIO = 0.012
MARGIN_Y_RATIO = 0.015

# 行ごと: 回転(度)、中心からの横・縦ずれ — 行書で暴れ狂うリズム（再現可能な固定値）
LINE_ANGLES_DEG = (-8.5, 11.0, -9.5)
LINE_OFFSET_X = (-72, 88, -65)
LINE_OFFSET_Y = (-38, 48, -42)

CACHE_DIR = Path.home() / ".cache" / "brush_message_gen"
OUT_JPEG = Path(__file__).resolve().parent.parent / "brush_message_4x3.jpg"
OUT_PNG = Path(__file__).resolve().parent.parent / "brush_message_4x3.png"


def _font_path() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / FONT_FILENAME
    if not path.exists():
        urllib.request.urlretrieve(FONT_URL, path)
    return path


def _render_line_rgba(text: str, font: ImageFont.FreeTypeFont, angle_deg: float) -> Image.Image:
    """Draw one line on transparent RGBA; return rotated image (expand=True)."""
    probe = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(probe)
    bb = d.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    # 文字ギリギリのキャンバス（従来の巨大パディングは回転後に不要な余白だけ増やす）
    m = 6
    layer = Image.new("RGBA", (tw + 2 * m, th + 2 * m), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer)
    ox = m - bb[0]
    oy = m - bb[1]
    d2.text((ox, oy), text, font=font, fill=(*FG, 255))
    if abs(angle_deg) < 0.01:
        return layer
    return layer.rotate(angle_deg, expand=True, resample=Image.BICUBIC)


def _layout_at_size(
    font_path: str,
    font_size: int,
    margin_x: int,
    margin_y: int,
    avail_w: int,
    avail_h: int,
) -> tuple[list[Image.Image], list[tuple[int, int]]] | None:
    """Build layers and paste positions that fit inside the margin box; else None."""
    font = ImageFont.truetype(font_path, font_size)
    layers: list[Image.Image] = []
    sizes: list[tuple[int, int]] = []

    for i, line in enumerate(TEXT_LINES):
        im = _render_line_rgba(line, font, LINE_ANGLES_DEG[i])
        layers.append(im)
        sizes.append(im.size)

    rh = [h for (_, h) in sizes]
    # タイトな行間で縦を最大化（画面いっぱい）
    gap = max(4, int(min(rh) * 0.02))
    total_h = sum(rh) + gap * (len(rh) - 1)

    # 仮配置: ブロック縦中央、各行はセンター + オフセット
    y0 = (avail_h - total_h) // 2
    cx_rel = avail_w // 2
    positions_rel: list[tuple[int, int]] = []
    y_cursor = y0

    for i, layer in enumerate(layers):
        w, h = sizes[i]
        cx = cx_rel + LINE_OFFSET_X[i]
        cy = y_cursor + h // 2 + LINE_OFFSET_Y[i]
        px = int(cx - w / 2)
        py = int(cy - h / 2)
        positions_rel.append((px, py))
        y_cursor += h + gap

    # 相対座標のバウンディングボックス
    min_x = min(p[0] for p, (w, _) in zip(positions_rel, sizes))
    max_x = max(p[0] + w for p, (w, _) in zip(positions_rel, sizes))
    min_y = min(p[1] for p in positions_rel)
    max_y = max(p[1] + h for p, (_, h) in zip(positions_rel, sizes))

    bw = max_x - min_x
    bh = max_y - min_y
    if bw > avail_w or bh > avail_h:
        return None

    # マージン内にブロック全体を中央寄せ
    shift_x = margin_x + (avail_w - bw) // 2 - min_x
    shift_y = margin_y + (avail_h - bh) // 2 - min_y
    positions = [(px + shift_x, py + shift_y) for px, py in positions_rel]

    # 最終チェック
    for (px, py), (w, h) in zip(positions, sizes):
        if px < margin_x or px + w > WIDTH - margin_x:
            return None
        if py < margin_y or py + h > HEIGHT - margin_y:
            return None

    return (layers, positions)


def main() -> None:
    font_path = _font_path()
    margin_x = int(WIDTH * MARGIN_X_RATIO)
    margin_y = int(HEIGHT * MARGIN_Y_RATIO)
    avail_w = WIDTH - 2 * margin_x
    avail_h = HEIGHT - 2 * margin_y

    lo, hi = 40, 520
    best: tuple[list[Image.Image], list[tuple[int, int]]] | None = None
    while lo <= hi:
        mid = (lo + hi) // 2
        fit = _layout_at_size(str(font_path), mid, margin_x, margin_y, avail_w, avail_h)
        if fit is not None:
            best = fit
            lo = mid + 1
        else:
            hi = mid - 1

    if best is None:
        raise RuntimeError("Could not fit text; increase canvas or reduce copy.")

    layers, positions = best
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    for layer, pos in zip(layers, positions):
        img.paste(layer, pos, layer)

    img.save(OUT_JPEG, "JPEG", quality=95, optimize=True)
    img.save(OUT_PNG, "PNG", optimize=True)
    print(f"Wrote {OUT_JPEG} and {OUT_PNG}")


if __name__ == "__main__":
    main()
