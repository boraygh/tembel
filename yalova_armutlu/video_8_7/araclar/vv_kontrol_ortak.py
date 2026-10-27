# Video-video çıktısını Blender girdisiyle karşılaştırır: zamana göre kenar korelasyonu (kompozisyon/hareket
# sadakati) ve yan yana pafta (üst Blender, alt Kling).  Kullanım: python3 vv_kontrol.py GIRDI.mp4 CIKTI.mp4 AD
import io, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 640, 360


def kareler(yol):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", yol, "-vf", f"fps=24,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)


def kenar(k):
    g = k.astype(np.float32).mean(2)
    e = np.abs(np.diff(g, axis=1, prepend=g[:, :1])) + np.abs(np.diff(g, axis=0, prepend=g[:1]))
    return np.asarray(Image.fromarray(np.clip(e * 3, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32)


