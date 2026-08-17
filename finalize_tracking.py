#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finalize tracking JSON: apply per-item offsets, fill earring nulls with drift."""
import json

SRC = r"D:\workspace\paulola_html\assets\jewelry-tracking.json"

# 偏移修正（%）：视觉验证发现 手链偏下、项链偏左
OFFSET = {
    "bracelet": (0.0, -5.0),
    "necklace": (3.0, 0.0),
    "ring": (0.0, 0.0),
    "earrings": (0.0, 0.0),
}
# 耳环段空缺的漂移轨迹（来自视觉定位：耳环随镜头右移，y 在上部）
EARRING_DRIFT = {
    6.50: (14.0, 40.0), 6.75: (16.0, 40.0), 7.00: (18.0, 39.5), 7.25: (20.0, 39.0),
    7.50: (22.0, 39.0), 7.75: (25.0, 38.5), 8.00: (28.0, 38.5), 8.25: (31.0, 38.0),
    8.50: (33.0, 38.0), 8.75: (35.0, 38.0), 9.00: (38.0, 37.5), 9.25: (41.0, 37.5),
    9.50: (45.0, 38.0), 9.75: (48.0, 38.0), 10.00: (52.0, 38.0),
}

def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)

    for item, samples in data.items():
        ox, oy = OFFSET.get(item, (0, 0))
        for s in samples:
            if s[1] is not None:
                s[1] = round(max(0.0, min(100.0, s[1] + ox)), 1)
            if s[2] is not None:
                s[2] = round(max(0.0, min(100.0, s[2] + oy)), 1)

    # 耳环空缺填充
    ear = data["earrings"]
    for s in ear:
        if s[1] is None:
            drift = EARRING_DRIFT.get(round(s[0], 2))
            if drift:
                s[1], s[2] = drift
    # 仍为空的（6.5 等）用相邻插值
    valid = [s for s in ear if s[1] is not None]
    for i, s in enumerate(ear):
        if s[1] is None:
            # 找最近有效
            best = min(valid, key=lambda v: abs(v[0] - s[0]))
            s[1], s[2] = best[1], best[2]

    with open(SRC, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    for item, samples in data.items():
        print(item, len(samples), "samples; first:", samples[0], "last:", samples[-1])

if __name__ == "__main__":
    main()
