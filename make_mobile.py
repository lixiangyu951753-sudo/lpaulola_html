#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate smart-crop portrait (9:16) version of the hero video.
Crop window 405x720 slides horizontally following jewelry focus waypoints."""
import subprocess, os

FFMPEG = r"C:\Users\PAULOLA\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe"
SRC = r"D:\workspace\paulola_html\assets\video-jewelry-showcase-web.mp4"
OUT = r"D:\workspace\paulola_html\assets\video-jewelry-showcase-mobile.mp4"

# Waypoints: (time_seconds, focus_center_x_px) on 1280-wide source
# bracelet 0-1.5s @48%, necklace/ring 1.5-6.5s @55%, earrings 6.5-10s drift right
WP = [
    (0.0, 614), (1.5, 614), (2.1, 704), (5.0, 704), (5.6, 704), (6.5, 704),
    (7.0, 200), (8.0, 358), (9.0, 486), (10.0, 704),
]

def lerp(a, b, t01):
    return a + (b - a) * t01

def build_expr(wp):
    # x(t) as nested if(lt(t, t_next), lerp_segment, ...)
    def seg(i):
        t0, c0 = wp[i]
        t1, c1 = wp[i + 1]
        if i == len(wp) - 2:
            return f"({c0}+{c1-c0}*(t-{t0})/{t1-t0:.4f})"
        return f"if(lt(t,{t1}),{c0}+{c1-c0}*(t-{t0})/{t1-t0:.4f},{seg(i+1)})"
    return seg(0)

expr = build_expr(WP)
# crop_left = center - width/2 ; clip to [0, 1280-405]
# 逗号必须转义为 \, 否则 ffmpeg 会按过滤器分隔符拆开表达式
crop_left = f"clip(({expr})-202.5,0,875)".replace(",", "\\,")
filtergraph = f"crop=405:720:{crop_left}:0,scale=720:1280:flags=lanczos,setsar=1"
print("FILTER:", filtergraph[:200], "...")

cmd = [FFMPEG, "-y", "-i", SRC, "-vf", filtergraph,
       "-c:v", "libx264", "-crf", "27", "-preset", "slow",
       "-an", "-movflags", "+faststart", "-pix_fmt", "yuv420p", OUT]
# 沙箱限制：子进程不能用管道捕获输出（EPERM），用继承 stdio
r = subprocess.run(cmd)
print("rc:", r.returncode)
print("size MB:", round(os.path.getsize(OUT) / 1e6, 2))
