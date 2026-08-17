#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test YOLO-World detection with diamond/gemstone prompts on key frames."""
from ultralytics import YOLOWorld

MODEL = "yolov8s-world.pt"
CLASSES = ["diamond", "brilliant cut diamond", "gemstone", "sparkling stone",
           "moissanite", "jewelry stone", "solitaire diamond"]

FRAMES = [
    ("d02", r"D:\workspace\paulola_html\frames\d02.png", "1s 手链"),
    ("d07", r"D:\workspace\paulola_html\frames\d07.png", "3s 项链"),
    ("d12", r"D:\workspace\paulola_html\frames\d12.png", "5.5s 戒指"),
    ("d19", r"D:\workspace\paulola_html\frames\d19.png", "9s 耳环"),
]

def main():
    model = YOLOWorld(MODEL)
    model.set_classes(CLASSES)
    for key, path, label in FRAMES:
        results = model.predict(path, conf=0.08, verbose=False, device="cuda")
        dets = []
        for r in results:
            if r.boxes is None:
                continue
            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                x1, y1, x2, y2 = [float(v) for v in box]
                dets.append({
                    "class": CLASSES[int(cls)],
                    "conf": round(float(conf), 3),
                    "center": (round((x1 + x2) / 2 / 1280 * 100, 1), round((y1 + y2) / 2 / 720 * 100, 1)),
                    "box": [round(x1), round(y1), round(x2), round(y2)],
                })
        print(f"== {key} ({label}) ==")
        if not dets:
            print("  (no detections)")
        for d in sorted(dets, key=lambda x: -x["conf"])[:6]:
            print(f"  {d['class']:22s} conf={d['conf']:.2f} center={d['center']}")

if __name__ == "__main__":
    main()
