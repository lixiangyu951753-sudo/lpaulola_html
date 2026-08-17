#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Annotate bright sparkle (diamond) positions on every frame with red markers."""
import os
import cv2
import numpy as np

SRC_DIR = r"D:\workspace\paulola_html\frames\src"
OUT_DIR = r"D:\workspace\paulola_html\frames\sparkle_ann"
THR = 200
MIN_AREA = 10
MAX_AREA = 5000
MAX_MARKERS = 8

def find_spots(gray):
    _, mask = cv2.threshold(gray, THR, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    spots = []
    for c in contours:
        area = cv2.contourArea(c)
        if MIN_AREA <= area <= MAX_AREA:
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            spots.append((cx, cy, area))
    spots.sort(key=lambda s: -s[2])
    return spots[:MAX_MARKERS]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    names = sorted(n for n in os.listdir(SRC_DIR) if n.startswith("f_") and n.endswith(".png"))
    for idx, name in enumerate(names):
        path = os.path.join(SRC_DIR, name)
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        spots = find_spots(gray)
        for cx, cy, area in spots:
            c = (int(cx), int(cy))
            r = max(6, int(np.sqrt(area) * 0.6))
            cv2.circle(img, c, r, (0, 0, 255), 3)          # 红圈
            cv2.line(img, (c[0] - r - 6, c[1]), (c[0] + r + 6, c[1]), (0, 0, 255), 2)
            cv2.line(img, (c[0], c[1] - r - 6), (c[0], c[1] + r + 6), (0, 0, 255), 2)
        cv2.imwrite(os.path.join(OUT_DIR, name), img)
        if idx % 60 == 0:
            print(f"  {idx}/{len(names)}")
    print("done")

if __name__ == "__main__":
    main()
