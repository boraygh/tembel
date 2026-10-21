# NB Pro girdisi: maskedeki ağaç / komşu ev / araç / insan bölgeleri maske-duyarlı Gauss ile
# yumuşatılır (yapay zekâ bunları gerçek fotoğraf olarak yeniden çizer); proje blokları, yollar,
# sahil ve deniz keskin kalır. Kullanım: python3 girdi_b.py K1 [K2 ...]
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from girdi_yap import maske_oku, girdi
from proj import proj

KAM = json.load(open("kameralar_b.json"))
KIYI_KORU = {"K3", "K4"}           # denizin göründüğü kareler: sahil bandı ve deniz keskin kalır


def izin(ad, W, H):
    """Kıyı hattının kara tarafı 1, deniz tarafı 0 (kara tarafı: kahraman bloğun olduğu taraf)."""
    pts = sorted(p for p in json.load(open(ad + "_kiyi.json")) if -600 < p[0] < W + 600)
    if len(pts) < 2:
        return np.ones((H, W), np.float32)
    ycut = np.interp(np.arange(W), [p[0] for p in pts], [p[1] for p in pts])
    k = KAM[ad]
    hx, hy = proj(k["konum"], k["hedef"], k["lens"], [(19.83, -54.54, k["kalk"])])[0]
    hx, hy = int(np.clip(hx * W, 0, W - 1)), (1 - hy) * H
    yy = np.arange(H)[:, None]
    return ((yy > ycut[None, :]) if hy > ycut[hx] else (yy < ycut[None, :])).astype(np.float32)


for ad in sys.argv[1:]:
    m = maske_oku(ad + "_maske.png")
    iz = izin(ad, *m.size) if ad in KIYI_KORU else np.ones(m.size[::-1], np.float32)
    print(ad, "yumuşatılabilir alan oranı %.2f" % iz.mean(), " maske beyaz oranı %.2f" % (np.asarray(m) > 127).mean())
    girdi(ad + "_render.png", m, ad + "_girdi.png", 4.5, 7, iz)
