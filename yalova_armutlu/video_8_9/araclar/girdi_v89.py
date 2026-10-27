# Nano Banana girdileri: maskeli bölgeler (komşu evler, ağaçlar) maske-duyarlı Gauss ile yumuşatılır.
# Kıyı koruması: A0'da (denizden bakış) kara kıyı hattının üstünde, balkon karelerinde (karadan
# denize bakış) altında kalır; deniz tarafı hiç yumuşatılmaz.
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "video", "araclar"))
from girdi_yap import maske_oku, girdi


def izin(ad, W, H):
    pts = sorted(p for p in json.load(open(f"{ad}_kiyi.json")) if -600 < p[0] < W + 600)
    ycut = np.interp(np.arange(W), [p[0] for p in pts], [p[1] for p in pts])
    yy = np.arange(H)[:, None]
    kara_ustte = ad == "A0"
    return ((yy < ycut[None, :]) if kara_ustte else (yy > ycut[None, :])).astype(np.float32)


for ad in sys.argv[1:]:
    m = maske_oku(f"{ad}_maske.png")
    iz = izin(ad, *m.size)
    print(f"{ad}: maske beyaz {(np.asarray(m) > 127).mean():.3f}, yumuşatılabilir alan {iz.mean():.3f}")
    girdi(f"{ad}_render.png", m, f"{ad}_girdi.png", 5.0 if ad == "A0" else 4.5, 9 if ad == "A0" else 7, iz)
