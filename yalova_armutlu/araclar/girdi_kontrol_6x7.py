# Revizyon kareleri için yardımcılar.
#   python3 girdi_kontrol_6x7.py girdi AD                 -> AD_girdi.png (yumuşatılmış yapay zekâ girdisi) + AD_girdi_k.jpg
#   python3 girdi_kontrol_6x7.py kontrol AD NB.png        -> karo korelasyonu, hizalama ve blok etiketli kırpım (AD_etiket.jpg)
#   python3 girdi_kontrol_6x7.py filigran NB.png CIKTI.png
# Başka yerleşim için: KAMERALAR=kameralar_7x6.json SIRA=7,6 python3 girdi_kontrol_6x7.py ...
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "video", "araclar"))   # girdi_yap, proj, filigran, hiza
from girdi_yap import maske_oku, izin_bolgesi, girdi
from proj import proj

K = json.load(open(os.environ.get("KAMERALAR", "kameralar.json")))
SOL, SAG = (int(v) for v in os.environ.get("SIRA", "6,7").split(","))   # 7104 / 7105 blok adedi (sağ üst görseli: 7,6)


def bloklar():
    out = []
    for ad, (u0, v0), (u1, v1), n in (("S", (-22.36, 64.30), (-20.86, -71.76), SOL), ("Ğ", (18.39, 63.37), (19.83, -54.54), SAG)):
        for k in range(n):
            f = k / (n - 1)
            out.append((ad, k, u0 + (u1 - u0) * f, v0 + (v1 - v0) * f))
    return out


if sys.argv[1] == "girdi":
    ad = sys.argv[2]
    m = maske_oku(f"{ad}_maske.png")
    iz = izin_bolgesi(f"{ad}_kiyi.json", *m.size)
    print(f"{ad}: maske beyaz oranı {(np.asarray(m) > 127).mean():.3f}, yumuşatılabilir alan {iz.mean():.3f}")
    girdi(f"{ad}_render.png", m, f"{ad}_girdi.png", 9.5, 23, iz)

elif sys.argv[1] == "kontrol":
    ad, nb = sys.argv[2], sys.argv[3]
    from hiza import hiza
    print("hizalama (skor, mod, ölçek, dx, dy):", hiza(f"{ad}_render.png", nb))
    C, T, L = K[ad]
    im = Image.open(nb).convert("RGB")
    W, H = im.size
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", max(24, W // 120))
    xs, ys = [], []
    for sira, k, u, v in bloklar():
        x, y = proj(C, T, L, [(u, v, 23.0)])[0]
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
    # karo korelasyonu (kompozisyon korunmuş mu)
    from PIL import ImageFilter
    def kenar(p):
        g = np.asarray(Image.open(p).convert("L").resize((960, 540), Image.LANCZOS), np.float32)
        e = np.abs(np.diff(g, axis=1, prepend=g[:, :1])) + np.abs(np.diff(g, axis=0, prepend=g[:1]))
        return np.asarray(Image.fromarray(np.clip(e * 3, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32)
    a, b = kenar(f"{ad}_render.png"), kenar(nb)
    t = np.array([[np.corrcoef(a[i*135:(i+1)*135, j*240:(j+1)*240].ravel(), b[i*135:(i+1)*135, j*240:(j+1)*240].ravel())[0, 1]
                   for j in range(4)] for i in range(4)])
    print("karo korelasyonları:"); [print("  " + "  ".join(f"{v:5.2f}" for v in r)) for r in t]
    print(f"  en düşük {t.min():.2f}  ortalama {t.mean():.2f}")

elif sys.argv[1] == "filigran":
    from filigran import uygula
    print(uygula(sys.argv[2], sys.argv[3], "sol_ust", perde=0.45))
