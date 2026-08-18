# -*- coding: utf-8 -*-
"""Download all product images from the manifest into product folders."""
import json
import os
import re
import shutil
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = r"D:\workspace\paulola_html\采集箱_最后两页图片"
MANIFEST = r"D:\workspace\paulola_html\采集箱_manifest.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": "https://www.dianxiaomi.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}

INVALID = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

def sanitize(name, maxlen=40):
    name = INVALID.sub("_", name).strip().strip(".")
    return name[:maxlen] if name else "未命名"

def norm(url):
    """Strip cache-busting query params so the same image isn't downloaded twice."""
    return url.split("?")[0].split("#")[0]

def ext_of(url):
    p = url.split("?")[0].split("/")[-1].lower()
    for e in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        if p.endswith(e):
            return e
    return ".jpg"

def download(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    tmp = dest + ".part"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f, 1024 * 256)
            if os.path.getsize(tmp) > 0:
                os.replace(tmp, dest)
                return True
        except Exception as e:
            if attempt == 2:
                print(f"FAIL {url} -> {e}", flush=True)
            time.sleep(1.5 * (attempt + 1))
    return False

def main():
    data = json.load(open(MANIFEST, encoding="utf-8"))
    items = data["items"]
    downloaded = {}          # norm url -> first saved file
    jobs = []                # (url, dest_file, norm)
    for it in items:
        page_dir = os.path.join(BASE, f"第{it['page']}页")
        prod_dir = os.path.join(page_dir, f"第{it['idx']:02d}个_{sanitize(it['name'])}")
        os.makedirs(prod_dir, exist_ok=True)
        for k, url in enumerate(it["images"], 1):
            dest = os.path.join(prod_dir, f"{k:03d}{ext_of(url)}")
            jobs.append((url, dest, norm(url), prod_dir))

    print(f"total jobs: {len(jobs)}", flush=True)

    def work(job):
        url, dest, n = job[0], job[1], job[2]
        if os.path.exists(dest):
            return (dest, True, "exists")
        if n in downloaded:
            try:
                shutil.copy2(downloaded[n], dest)
                return (dest, True, "copy")
            except Exception as e:
                print(f"COPY FAIL {dest}: {e}", flush=True)
        if download(url, dest):
            downloaded.setdefault(n, dest)
            return (dest, True, "dl")
        return (dest, False, "fail")

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(work, j) for j in jobs]
        for f in as_completed(futs):
            dest, status, how = f.result()
            if status:
                ok += 1
            else:
                fail += 1
                print(f"  FAILED: {dest}", flush=True)
    print(f"DONE ok={ok} fail={fail}", flush=True)

if __name__ == "__main__":
    sys.exit(main())
