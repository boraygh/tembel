# Nano Banana Pro çıktısını Blender karesiyle karşılaştırır.
#   python3 kontrol.py AD NB.png
# -> hizalama (skor, mod, ölçek, dx, dy), 4x4 karo kenar korelasyonu,
#    AD_kars.jpg (üstte Blender girdisi, altta NB; ufuk çizgisi işaretli),
#    A0 için blok etiketli kırpım AD_etiket.jpg (8 + 9 blok sayımı)
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "video", "araclar"))
from hiza import hiza

K = json.load(open("kameralar.json"))
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"


def proj(k, P, aspect=9 / 16):
    C, T = np.array(k["konum"], float), np.array(k["hedef"], float)
    F = T - C; F /= np.linalg.norm(F)
    R = np.cross(F, [0, 0, 1.0]); R /= np.linalg.norm(R)
    U = np.cross(R, F)
    P = np.atleast_2d(np.array(P, float)) - C
    d = P @ F
    xs = k["lens"] * (P @ R) / d
    ys = k["lens"] * (P @ U) / d
    return np.stack([0.5 + xs / 36, 0.5 + (ys - k["kay"] * 36) / (36 * aspect)], 1)


def bloklar():
    out = []
    for ad, (u0, v0), (u1, v1), n in (("S", (-22.36, 64.30), (-20.86, -71.76), 8), ("Ğ", (18.39, 63.37), (19.83, -54.54), 9)):
        for k in range(n):
            f = k / (n - 1)
            out.append((ad, k, u0 + (u1 - u0) * f, v0 + (v1 - v0) * f))
    return out


def kenar(p):
    g = np.asarray(Image.open(p).convert("L").resize((960, 540), Image.LANCZOS), np.float32)
    e = np.abs(np.diff(g, axis=1, prepend=g[:, :1])) + np.abs(np.diff(g, axis=0, prepend=g[:1]))
    return np.asarray(Image.fromarray(np.clip(e * 3, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32)


ad, nb = sys.argv[1], sys.argv[2]
kam = K[ad]
print("hizalama (skor, mod, ölçek, dx, dy):", hiza(f"{ad}_render.png", nb))
a, b = kenar(f"{ad}_render.png"), kenar(nb)
t = np.array([[np.corrcoef(a[i*135:(i+1)*135, j*240:(j+1)*240].ravel(), b[i*135:(i+1)*135, j*240:(j+1)*240].ravel())[0, 1]
               for j in range(4)] for i in range(4)])
print("karo korelasyonları:"); [print("  " + "  ".join(f"{v:5.2f}" for v in r)) for r in t]
print(f"  en düşük {np.nanmin(t):.2f}  ortalama {np.nanmean(t):.2f}")

# ufuk: kameradan 20 km uzaktaki deniz seviyesi noktası
ileri = np.array(kam["hedef"], float) - np.array(kam["konum"], float); ileri[2] = 0; ileri /= np.linalg.norm(ileri)
uf = proj(kam, [np.array(kam["konum"], float) + ileri * 20000 - [0, 0, kam["konum"][2]]])[0]
print(f"ufuk (Blender): y = {(1 - uf[1]):.3f} (üstten oran)")

W, H = 1600, 900
g = Image.open(f"{ad}_girdi.png").convert("RGB").resize((W, H), Image.LANCZOS)
n = Image.open(nb).convert("RGB").resize((W, H), Image.LANCZOS)
c = Image.new("RGB", (W, 2 * H + 10), (0, 0, 0))
c.paste(g, (0, 0)); c.paste(n, (0, H + 10))
d = ImageDraw.Draw(c)
f = ImageFont.truetype(FONT, 30)
yuf = (1 - uf[1]) * H
for y0 in (0, H + 10):
    if 0 < yuf < H:
        d.line([(0, y0 + yuf), (W, y0 + yuf)], fill=(255, 40, 40), width=2)
d.text((12, 8), "BLENDER GİRDİSİ", font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
d.text((12, H + 18), "NANO BANANA PRO", font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
c.thumbnail((1400, 1600), Image.LANCZOS)
c.save(f"{ad}_kars.jpg", quality=86)

if kam["blok"] is None:
    im = Image.open(nb).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, max(24, W // 120))
    xs, ys = [], []
    for sira, k, u, v in bloklar():
        x, y = proj(kam, [(u, v, 23.0)])[0]
        X, Y = x * W, (1 - y) * H
        xs.append(X); ys.append(Y)
        renk = (255, 60, 60) if sira == "S" else (40, 150, 255)
        r = W // 300
        d.ellipse([X - r, Y - r, X + r, Y + r], fill=renk, outline=(255, 255, 255), width=max(2, r // 3))
        d.text((X + r + 4, Y - 2 * r), f"{sira}{k + 1}", font=f, fill=renk, stroke_width=3, stroke_fill=(0, 0, 0))
    x0, x1 = max(0, min(xs) - W * 0.12), min(W, max(xs) + W * 0.12)
    y0, y1 = max(0, min(ys) - H * 0.08), min(H, max(ys) + H * 0.30)
    k = im.crop((int(x0), int(y0), int(x1), int(y1)))
    k.thumbnail((1600, 1100), Image.LANCZOS)
    k.save(f"{ad}_etiket.jpg", quality=88)
