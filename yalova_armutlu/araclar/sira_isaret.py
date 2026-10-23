# Önizleme karesine iki sıranın blok gövdelerini (projeksiyonla) renkli işaretler; sıraların ayrışmasını ölçer.
import os, sys, json, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video", "araclar"))
from proj import proj
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 18)

def bloklar():
    out = []
    for ad, (u0, v0), (u1, v1), n, xb, yh in (("S", (-22.36, 64.30), (-20.86, -71.76), 6, 12.92, 5.61),
                                              ("Ğ", (18.39, 63.37), (19.83, -54.54), 7, 11.67, 6.15)):
        for k in range(n):
            f = k / (n - 1)
            out.append((ad, k, u0 + (u1 - u0) * f, v0 + (v1 - v0) * f, xb, yh))
    return out

def hull(p):
    p = sorted(map(tuple, p))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, hi = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], q) <= 0: hi.pop()
        hi.append(q)
    return lo[:-1] + hi[:-1]

def isaretle(png, C, T, L, cikti):
    im = Image.open(png).convert("RGBA")
    W, H = im.size
    kat = {"S": Image.new("L", (W, H), 0), "Ğ": Image.new("L", (W, H), 0)}
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for ad, k, u, v, xb, yh in bloklar():
        pts = [(u + sx * xb, v + sy * yh, z) for sx in (-1, 1) for sy in (-1, 1) for z in (0.0, 19.0)]
        p = proj(C, T, L, pts)
        poly = [(x * W, (1 - y) * H) for x, y in hull(p)]
        renk = (255, 60, 60, 90) if ad == "S" else (40, 140, 255, 90)
        d.polygon(poly, fill=renk, outline=renk[:3] + (255,))
        ImageDraw.Draw(kat[ad]).polygon(poly, fill=255)
        cx, cy = proj(C, T, L, [(u, v, 21.0)])[0]
        d.text((cx * W - 10, (1 - cy) * H - 22), f"{ad}{k + 1}", font=F, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
    a, b = np.asarray(kat["S"]) > 0, np.asarray(kat["Ğ"]) > 0
    ortusme = (a & b).sum() / max(1, min(a.sum(), b.sum()))
    Image.alpha_composite(im, ov).convert("RGB").save(cikti, quality=88)
    return ortusme

if __name__ == "__main__":
    K = json.load(open("kameralar.json"))
    for ad in sys.argv[1:]:
        C, T, L = K[ad]
        print(ad, "iki sıranın görüntüde üst üste binme oranı: %.2f" % isaretle(f"oniz_{ad}.png", C, T, L, f"isaret_{ad}.jpg"))
