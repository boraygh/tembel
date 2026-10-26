# K2 girdisi: K1 fotoğrafı (sabit kamera) + yalnız değişen bölgede Blender K2 karesi.
# Değişen bölge = bloğun K1'deki ve K2'deki görünen silueti (öndeki palmiyeler hariç) + kayan gölgeler.
# "son" modu: NB Pro çıktısını K1 fotoğrafına geri oturtur (çevre iki karede birebir aynı kalır).
# Kullanım: python3 k2_bilesik.py            -> K2_bilesik.png (NB Pro girdisi)
#           python3 k2_bilesik.py son NB.png -> K2_foto.png
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from girdi_yap import gblur

W, H = 1920, 1080


def oku(p):
    return np.asarray(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), np.float32) / 255


def alfa(p):
    return np.asarray(Image.open(p), np.float32)[..., 3] / 255


def gen(a, n):                       # n piksel büyüt (ikili maske)
    im = Image.fromarray((a > 0.5).astype(np.uint8) * 255)
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * n + 1)), np.float32) / 255


def bosluk_doldur(a):
    """Kenara bağlı olmayan siyah adacıkları (delikleri) doldurur."""
    im = Image.fromarray((a > 0.5).astype(np.uint8) * 255).convert("L")
    w, h = im.size
    tam = Image.new("L", (w + 2, h + 2), 0)
    tam.paste(im, (1, 1))
    ImageDraw.floodfill(tam, (0, 0), 128)
    t = np.asarray(tam, np.uint8)[1:-1, 1:-1]
    return (t != 128).astype(np.float32)


s1, s2 = alfa("K1_siluet.png"), alfa("K2_siluet.png")
r1, r2 = oku("K1_render.png"), oku("K2_render.png")
sil = np.maximum(gen(s1, 4), gen(s2, 2))
fark = np.abs(r1 - r2).max(axis=2) * (1 - gen(sil, 3))
g = Image.fromarray(((fark > 0.05) * 255).astype(np.uint8))
g = g.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))      # ince çizgileri (yaprak kenarı) at
g = g.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(5))
golge = np.asarray(g, np.float32) / 255
deg = np.maximum(sil, golge)
print("değişen alan oranı %.3f (siluet %.3f, gölge %.3f)" % (deg.mean(), sil.mean(), golge.mean()))
k1 = oku("K1_foto.png")

if len(sys.argv) > 2 and sys.argv[1] == "son":
    nb = oku(sys.argv[2])
    Mf = gen(bosluk_doldur(deg), 12)
    Mf = np.clip(gblur(Mf, 4.0), 0, 1)
    out = k1 * (1 - Mf[..., None]) + nb * Mf[..., None]
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save("K2_foto.png")
    Image.fromarray((Mf * 255).astype(np.uint8)).save("K2_son_maske.png")
    print("K2_foto.png tamam")
else:
    Mi = np.clip(gblur(deg, 1.2), 0, 1)
    g2 = oku("K2_girdi.png")
    out = k1 * (1 - Mi[..., None]) + g2 * Mi[..., None]
    o = Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))
    o.save("K2_bilesik.png")
    o.resize((1280, 720), Image.LANCZOS).save("K2_bilesik_k.jpg", quality=90)
    Image.fromarray((Mi * 255).astype(np.uint8)).save("K2_degisen.png")
