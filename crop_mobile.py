#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic smart-crop 9:16 mobile version.
Per-frame crop x computed in pure Python from focus waypoints (no ffmpeg expression).
Input: frames/src/f_%04d.png (1280x720)  Output: frames/mob/mob_%04d.png (720x1280)
"""
import os
from PIL import Image

SRC_DIR = r"D:\workspace\paulola_html\frames\src"
OUT_DIR = r"D:\workspace\paulola_html\frames\mob"
FPS = 24
SRC_W, SRC_H = 1280, 720
CROP_W = 405          # 720 * 9/16
CROP_H = 720
OUT_W, OUT_H = 720, 1280

# Waypoints (time_s, focus_center_x_px). bracelet->necklace->ring->earrings(drift right)
WP = [
    (0.0, 614), (1.5, 614), (2.1, 704), (5.0, 704), (5.6, 704), (6.5, 704),
    (7.0, 200), (8.0, 358), (9.0, 486), (10.0, 704),
]

def center_at(t):
    if t <= WP[0][0]:
        return WP[0][1]
    for i in range(len(WP) - 1):
        t0, c0 = WP[i]
        t1, c1 = WP[i + 1]
        if t < t1:
            return c0 + (c1 - c0) * (t - t0) / (t1 - t0)
    return WP[-1][1]

def main():
    names = sorted(n for n in os.listdir(SRC_DIR) if n.startswith("f_") and n.endswith(".png"))
    print("frames:", len(names))
    for idx, name in enumerate(names):
        t = idx / FPS
        cx = center_at(t)
        left = int(round(cx - CROP_W / 2))
        left = max(0, min(SRC_W - CROP_W, left))
        with Image.open(os.path.join(SRC_DIR, name)) as im:
            box = (left, 0, left + CROP_W, CROP_H)
            tile = im.crop(box).resize((OUT_W, OUT_H), Image.LANCZOS)
            tile.save(os.path.join(OUT_DIR, f"mob_{idx:04d}.png"))
    print("done")

if __name__ == "__main__":
    main()
