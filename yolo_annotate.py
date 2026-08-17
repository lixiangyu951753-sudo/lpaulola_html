#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Annotate every frame of the hero video with YOLO-World detection boxes.
Outputs annotated PNGs -> encoded to an mp4 for visual inspection.
"""
import os
from ultralytics import YOLOWorld

MODEL = "yolov8s-world.pt"
SRC_DIR = r"D:\workspace\paulola_html\frames\src"
OUT_DIR = r"D:\workspace\paulola_html\frames\yolo_ann"
CLASSES = ["bracelet", "necklace", "ring", "earring", "earrings",
           "diamond bracelet", "diamond necklace", "diamond ring", "diamond earring"]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    names = sorted(n for n in os.listdir(SRC_DIR) if n.startswith("f_") and n.endswith(".png"))
    print("frames:", len(names))
    model = YOLOWorld(MODEL)
    model.set_classes(CLASSES)
    for idx, name in enumerate(names):
        path = os.path.join(SRC_DIR, name)
        results = model.predict(path, conf=0.10, verbose=False, device="cuda")
        ann = results[0].plot()          # BGR numpy with boxes+labels
        out_path = os.path.join(OUT_DIR, name)
        import cv2
        cv2.imwrite(out_path, ann)
        if idx % 60 == 0:
            print(f"  {idx}/{len(names)}")
    print("annotated frames saved to", OUT_DIR)

if __name__ == "__main__":
    main()
