#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YOLO-World jewelry detection test on hero video key frames."""
from ultralytics import YOLOWorld

MODEL = "yolov8s-world.pt"  # auto-downloads on first run (~23MB)

def detect(frame_path, classes):
    model = YOLOWorld(MODEL)
    model.set_classes(classes)
    results = model.predict(frame_path, conf=0.10, verbose=False)
    out = []
    for r in results:
        if r.boxes is None:
            continue
        for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            x1, y1, x2, y2 = [float(v) for v in box]
            out.append({
                "class": classes[int(cls)],
                "conf": round(float(conf), 3),
                "box": [round(x1), round(y1), round(x2), round(y2)],
            })
    return out

FRAMES = [
    ("d02", r"D:\workspace\paulola_html\frames\d02.png", "1s 手链段"),
    ("d07", r"D:\workspace\paulola_html\frames\d07.png", "3s 项链段"),
    ("d12", r"D:\workspace\paulola_html\frames\d12.png", "5.5s 戒指段"),
    ("d19", r"D:\workspace\paulola_html\frames\d19.png", "9s 耳环段"),
]
CLASSES = ["bracelet", "necklace", "ring", "earrings"]

for key, path, label in FRAMES:
    dets = detect(path, CLASSES)
    print(f"== {key} ({label}) ==")
    if not dets:
        print("  (no detections)")
    for d in dets:
        print(f"  {d['class']:10s} conf={d['conf']:.2f} box={d['box']}")
