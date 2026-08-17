#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Overlay tracked jewelry positions on key frames for visual verification."""
import json
from PIL import Image, ImageDraw

TRACK = r"D:\workspace\paulola_html\assets\jewelry-tracking.json"
FRAME_DIR = r"D:\workspace\paulola_html\frames\src"

def pos_at(data, item, t):
    pts = data[item]
    best = min(pts, key=lambda p: abs(p[0] - t))
    return best[1], best[2]

def main():
    with open(TRACK, encoding="utf-8") as f:
        data = json.load(f)
    checks = [
        ("bracelet", 1.0, "d02", 24),    # 1s
        ("necklace", 3.0, "d07", 72),    # 3s
        ("ring", 5.5, "d12", 132),       # 5.5s
        ("earrings", 9.0, "d19", 216),   # 9s
    ]
    for item, t, name, n in checks:
        x, y = pos_at(data, item, t)
        if x is None:
            print(f"{item}@{t}s: NO DATA")
            continue
        frame = f"{FRAME_DIR}\\f_{n:04d}.png"
        im = Image.open(frame).convert("RGB")
        d = ImageDraw.Draw(im)
        px, py = int(x / 100 * 1280), int(y / 100 * 720)
        r = 14
        d.ellipse((px - r, py - r, px + r, py + r), outline=(255, 0, 0), width=4)
        d.line((px - r - 8, py, px + r + 8, py), fill=(255, 0, 0), width=3)
        d.line((px, py - r - 8, px, py + r + 8), fill=(255, 0, 0), width=3)
        out = f"D:\\workspace\\paulola_html\\frames\\track_{item}.png"
        im.save(out)
        print(f"{item}@{t}s -> ({x}, {y})% saved {out}")

if __name__ == "__main__":
    main()
