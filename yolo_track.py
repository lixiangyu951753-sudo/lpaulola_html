#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO-World per-frame jewelry tracking v2.
Adds region priors + strict class matching to avoid wrong lock-ons.
"""
import os, json
from ultralytics import YOLOWorld

MODEL = "yolov8s-world.pt"
SRC_DIR = r"D:\workspace\paulola_html\frames\src"
OUT_JSON = r"D:\workspace\paulola_html\assets\jewelry-tracking.json"
FPS = 24
W, H = 1280, 720

# item, start, end, primary_class, prompt_classes, region (xmin,xmax,ymin,ymax in 0-1)
SEGMENTS = [
    ("bracelet", 0.0, 1.5, "bracelet", ["bracelet", "diamond bracelet"], (0.05, 0.95, 0.30, 0.98)),
    ("necklace", 1.5, 5.0, "necklace", ["necklace", "diamond necklace", "pendant"], (0.15, 0.85, 0.05, 0.60)),
    ("ring",     5.0, 6.5, "ring", ["ring", "diamond ring"], (0.05, 0.95, 0.30, 0.98)),
    ("earrings", 6.5, 10.0, "earring", ["earring", "earrings", "diamond earring"], (0.05, 0.95, 0.00, 0.55)),
]

def segment_of(t):
    for item, s, e, _, _, _ in SEGMENTS:
        if s <= t < e:
            return item
    return None

def main():
    names = sorted(n for n in os.listdir(SRC_DIR) if n.startswith("f_") and n.endswith(".png"))
    print("frames:", len(names))
    model = None
    current = None
    timeline = {item: [] for item, *_ in SEGMENTS}

    for idx, name in enumerate(names):
        t = idx / FPS
        item = segment_of(t)
        if item is None:
            continue
        seg = next(s for s in SEGMENTS if s[0] == item)
        _, s, e, primary, classes, (rx0, rx1, ry0, ry1) = seg
        if model is None or current != item:
            model = YOLOWorld(MODEL)
            model.set_classes(classes)
            current = item
        results = model.predict(os.path.join(SRC_DIR, name), conf=0.10, verbose=False, device="cuda")
        best = None
        for r in results:
            if r.boxes is None:
                continue
            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                c = classes[int(cls)]
                x1, y1, x2, y2 = [float(v) for v in box]
                cx = (x1 + x2) / 2 / W
                cy = (y1 + y2) / 2 / H
                # 区域先验过滤
                if not (rx0 <= cx <= rx1 and ry0 <= cy <= ry1):
                    continue
                # 严格主类优先
                cls_ok = (c == primary)
                score = float(conf) * (1.0 if cls_ok else 0.35)
                if best is None or score > best[0]:
                    best = (score, cx, cy)
        timeline[item].append((t, best[1] if best else None, best[2] if best else None))
        if idx % 60 == 0:
            print(f"  {idx}/{len(names)} {item}")

    out = {}
    for item, *_ in SEGMENTS:
        pts = timeline[item]
        times = [p[0] for p in pts]
        # 前向填充缺失
        xs, ys = [], []
        last = None
        for p in pts:
            if p[1] is not None:
                last = p
            xs.append(last[1] if last else None)
            ys.append(last[2] if last else None)
        def smooth(arr):
            r = list(arr)
            for i in range(2, len(arr) - 2):
                win = [v for v in arr[i-2:i+3] if v is not None]
                if len(win) >= 3 and arr[i] is not None:
                    r[i] = sorted(win)[len(win)//2]
            return r
        xs, ys = smooth(xs), smooth(ys)
        samples = []
        tt = times[0]
        while tt <= times[-1] + 1e-6:
            i = min(range(len(times)), key=lambda k: abs(times[k] - tt))
            samples.append([round(tt, 2), round(xs[i] * 100, 1) if xs[i] is not None else None,
                            round(ys[i] * 100, 1) if ys[i] is not None else None])
            tt += 0.25
        out[item] = samples
        print(f"{item}: {len(samples)} samples")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("saved:", OUT_JSON)

if __name__ == "__main__":
    main()
