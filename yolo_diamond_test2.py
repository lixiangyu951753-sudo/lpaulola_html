#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try (a) YOLO-World at very low conf with more prompts, and
(b) OpenCV bright-spot (diamond sparkle) detection on key frames."""
import cv2
import numpy as np
from ultralytics import YOLOWorld

MODEL = "yolov8s-world.pt"
CLASSES = ["diamond", "gem", "gemstone", "jewel", "jewelry", "sparkle", "bright object"]

FRAMES = [
    ("d02", r"D:\workspace\paulola_html\frames\d02.png", "1s 手链"),
    ("d07", r"D:\workspace\paulola_html\frames\d07.png", "3s 项链"),
    ("d12", r"D:\workspace\paulola_html\frames\d12.png", "5.5s 戒指"),
    ("d19", r"D:\workspace\paulola_html\frames\d19.png", "9s 耳环"),
]

def bright_spots(path, thr=200, min_area=12, max_area=4000):
    img = cv2.imread(path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, thr, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    spots = []
    for c in contours:
        area = cv2.contourArea(c)
        if min_area <= area <= max_area:
            M = cv2.moments(c)
            if M["m00"] == 0:
                continue
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            spots.append((cx / 1280 * 100, cy / 720 * 100, int(area)))
    spots.sort(key=lambda s: -s[2])
    return spots

def main():
    print("== YOLO conf=0.01 ==")
    model = YOLOWorld(MODEL)
    model.set_classes(CLASSES)
    for key, path, label in FRAMES:
        results = model.predict(path, conf=0.01, verbose=False, device="cuda")
        n = 0
        for r in results:
            if r.boxes is not None:
                n += len(r.boxes)
        print(f"  {key}: {n} yolo boxes")
    print("== OpenCV bright spots (top 5) ==")
    for key, path, label in FRAMES:
        spots = bright_spots(path)
        top = ", ".join(f"({s[0]:.1f}%,{s[1]:.1f}%,a{s[2]})" for s in spots[:5])
        print(f"  {key} ({label}): {top}")

if __name__ == "__main__":
    main()
