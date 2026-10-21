# B seçeneği anahtar kare kameraları: K0 doğrultusunda yaklaşma, aynı noktadan yükselme, 90°'lik yörünge.
import math, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proj import proj

U, V = 19.83, -54.54              # 7105-G
XB, YH, H, KULE = 11.67, 6.15, 16.1, 19.0
C0 = (134.9, -193.9, 60.8)        # K0 = CAM_YAKIN
YON0 = math.degrees(math.atan2(C0[0] - U, C0[1] - V)) % 360


def kameralar(L=14.0, Dh=102.0, Zc=58.0, tz=17.0, lens=50.0):
    out = {}
    for ad, d in (("K1", 0), ("K2", 0), ("K3", -90), ("K4", -180), ("K5", -270)):
        b = math.radians(YON0 + d)
        out[ad] = dict(konum=(U + Dh * math.sin(b), V + Dh * math.cos(b), Zc),
                       hedef=(U, V, tz), lens=lens, kalk=0.0 if ad == "K1" else L)
    return out


def kutu(kalk):
    return [(U + sx * XB, V + sy * YH, z + kalk) for sx in (-1, 1) for sy in (-1, 1) for z in (0, H)] + \
           [(U + sx * 3.6, V + sy * 1.9, KULE + kalk) for sx in (-1, 1) for sy in (-1, 1)]


if __name__ == "__main__":
    L, Dh, Zc, tz = (float(a) for a in sys.argv[1:5]) if len(sys.argv) > 4 else (14, 102, 58, 17)
    print(f"K0 yönü {YON0:.1f}°")
    for ad, k in kameralar(L, Dh, Zc, tz).items():
        p = proj(k["konum"], k["hedef"], k["lens"], kutu(k["kalk"]))
        z = proj(k["konum"], k["hedef"], k["lens"], kutu(0)[:8:2])   # zemin izi (z=0 köşeleri)
        d = math.degrees(math.atan2(Zc - tz, Dh))
        print(f"{ad}: C=({k['konum'][0]:.1f},{k['konum'][1]:.1f},{Zc}) eğim {d:.1f}°  blok x {p[:,0].min():.2f}-{p[:,0].max():.2f} "
              f"y {p[:,1].min():.2f}-{p[:,1].max():.2f}  | zemin izi y {z[:,1].min():.2f}-{z[:,1].max():.2f}")
