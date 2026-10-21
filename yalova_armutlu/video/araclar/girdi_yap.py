# Yapay zekâ girdisi: maskeli bölgeleri (komşu evler, ağaçlar, tepeler / peyzaj) maske-duyarlı
# Gauss ile yumuşatır; proje, yollar, sahil ve deniz keskin kalır.
# Kullanım: python3 girdi_yap.py GENEL_RENDER BLOK_RENDER MASKE_GENEL MASKE_BLOK KIYI_JSON CIKTI_ONEK
import json
import sys

import numpy as np
from PIL import Image, ImageFilter


def gblur(a, s):
    r = int(3 * s)
    x = np.arange(-r, r + 1, dtype=np.float32)
    k = np.exp(-x * x / (2 * s * s))
    k /= k.sum()
    for ax in (0, 1):
        pad = [(0, 0)] * a.ndim
        pad[ax] = (r, r)
        p = np.pad(a, pad, mode="reflect")
        out = np.zeros_like(a)
        n = a.shape[ax]
        for i, w in enumerate(k):
            sl = [slice(None)] * a.ndim
            sl[ax] = slice(i, i + n)
            out += w * p[tuple(sl)]
        a = out
    return a


def maske_oku(yol):
    a = np.asarray(Image.open(yol)).astype(np.float32) / 255
    return Image.fromarray((a[..., 0] * a[..., 3] * 255).astype(np.uint8))


def izin_bolgesi(kiyi_json, W, H):
    h = sorted(p for p in json.load(open(kiyi_json)) if -600 < p[0] < W + 600)
    ycut = np.interp(np.arange(W), [p[0] for p in h], [p[1] for p in h])
    return (np.arange(H)[:, None] < ycut[None, :]).astype(np.float32)


def girdi(kaynak, maske, cikti, sigma, kapama, sinir=None):
    org = np.asarray(Image.open(kaynak).convert("RGB"), dtype=np.float32) / 255
    m = maske.point(lambda v: 255 if v > 127 else 0)
    m = m.filter(ImageFilter.MaxFilter(kapama)).filter(ImageFilter.MinFilter(kapama))
    m = m.filter(ImageFilter.MaxFilter(5))
    sert = np.asarray(m, dtype=np.float32) / 255
    if sinir is not None:
        sert = sert * sinir
    yum = gblur(sert, 1.5)
    pay = gblur(org * sert[..., None], sigma)
    payda = gblur(sert, sigma)[..., None]
    bul = np.where(payda > 1e-3, pay / np.maximum(payda, 1e-3), org)
    out = org * (1 - yum[..., None]) + bul * yum[..., None]
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(cikti)
    k = Image.open(cikti)
    k.thumbnail((1400, 1400))
    k.save(cikti.replace(".png", "_k.jpg"), quality=88)
    print(cikti, "tamam")


if __name__ == "__main__":
    genel, blok, m_genel, m_blok, kiyi, onek = sys.argv[1:7]
    mg = maske_oku(m_genel)
    girdi(genel, mg, onek + "_genel.png", 6.5, 15, izin_bolgesi(kiyi, *mg.size))
    girdi(blok, maske_oku(m_blok), onek + "_blok.png", 5.0, 7)
