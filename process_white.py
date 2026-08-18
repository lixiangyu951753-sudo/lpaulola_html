# -*- coding: utf-8 -*-
"""
白底产品图 -> 暗调奢华展示图（黑绒 + 金色光斑 + 投影）
用法: python process_white.py <产品文件夹路径> <输出路径> [画布边长]
"""
import os
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

def pick_whitest(folder):
    """在文件夹里挑四角最白的图"""
    best, bestscore = None, -1
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        try:
            im = Image.open(os.path.join(folder, f)).convert("RGB")
            im.thumbnail((64, 64))
            a = np.asarray(im, dtype=np.int16)
            corners = np.concatenate([a[:3, :3].reshape(-1, 3), a[:3, -3:, :].reshape(-1, 3),
                                      a[-3:, :3].reshape(-1, 3), a[-3:, -3:, :].reshape(-1, 3)])
            mn = int(corners.min(axis=1).min())
            if mn > bestscore:
                best, bestscore = f, mn
        except Exception:
            pass
    return best, bestscore

def keyout_white(img):
    """按四角背景色做 alpha 抠图 + 去白边(defringe)"""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    bg = arr[:4, :4].reshape(-1, 3).mean(axis=0)  # 左上角采样作背景色
    d = np.max(np.abs(arr - bg), axis=2)          # 与背景的最大通道差
    alpha = np.clip((d - 12) * 14.0, 0, 255)      # 12~30 灰度区间羽化
    alpha = alpha[..., None]
    # defringe: 从半透明像素里剔除背景色成分 (标准 unpremultiply)
    rgb = (arr * 255.0 - bg[None, None, :] * (255.0 - alpha)) / np.maximum(alpha, 1e-3)
    rgb = np.clip(rgb, 0, 255)
    rgba = np.dstack([rgb, alpha]).astype(np.uint8)
    out = Image.fromarray(rgba, "RGBA")
    # 边缘轻微羽化
    a = out.split()[3].filter(ImageFilter.GaussianBlur(0.6))
    out.putalpha(a)
    return out

def dark_bg(size, center=(0.48, 0.42)):
    """黑绒+金色光斑背景"""
    w = h = size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = int(w * center[0]), int(h * center[1])
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / (max(w, h) * 0.62)
    inner = np.array([64, 48, 30])    # 暖棕金 #40301E
    outer = np.array([8, 8, 8])       # 近黑 #080808
    t = np.clip(dist, 0, 1.15)[..., None]
    t = np.clip(t, 0, 1)
    bg = inner * (1 - t) + outer * t
    img = Image.fromarray(bg.astype(np.uint8), "RGB").convert("RGBA")

    # 金色散景光斑
    rng = np.random.default_rng(7)
    blob = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw = None
    from PIL import ImageDraw
    dr = ImageDraw.Draw(blob)
    for _ in range(7):
        bw = int(rng.integers(90, 260))
        bx, by = int(rng.normal(w * 0.5, w * 0.30)), int(rng.normal(h * 0.42, h * 0.30))
        al = int(rng.integers(18, 46))
        dr.ellipse([bx - bw // 2, by - bw // 2, bx + bw // 2, by + bw // 2], fill=(196, 163, 90, al))
    blob = blob.filter(ImageFilter.GaussianBlur(70))
    img = Image.alpha_composite(img, blob)

    # 暗角
    vig = np.clip(dist * 0.55, 0, 0.55)
    a2 = img.split()[3].point(lambda v: v)
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    rgb *= (1 - vig[..., None] * 0.85)
    img = Image.fromarray(rgb.astype(np.uint8), "RGB")
    return img

def compose(product, bg, size):
    """产品放大到 58% 画布高，居中偏上，加投影"""
    bg = bg.convert("RGBA")
    max_h = int(size * 0.58)
    if product.height > max_h:
        product = product.resize((int(product.width * max_h / product.height), max_h), Image.LANCZOS)
    mask = product.split()[3]
    # 投影
    shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    sh = Image.new("RGBA", product.size, (0, 0, 0, 190))
    sh.putalpha(mask.point(lambda v: int(v * 0.65)))
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    sx = (bg.width - sh.width) // 2
    sy = int(bg.height * 0.46) + 26
    shadow.paste(sh, (sx, sy), sh)
    bg = Image.alpha_composite(bg, shadow)
    # 产品
    px = (bg.width - product.width) // 2
    py = int(bg.height * 0.46) - product.height // 2 + 6
    bg.paste(product, (px, py), product)
    return bg

def main():
    folder = sys.argv[1]
    out = sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
    f, score = pick_whitest(folder)
    print(f"use {f} (whiteness {score})")
    src = Image.open(os.path.join(folder, f)).convert("RGB")
    src.thumbnail((size, size), Image.LANCZOS)
    prod = keyout_white(src)
    prod = ImageEnhance.Contrast(prod).enhance(1.06)
    bg = dark_bg(size)
    final = compose(prod, bg, size).convert("RGB")
    final.save(out, "JPEG", quality=92)
    print("saved", out, final.size)

if __name__ == "__main__":
    main()
