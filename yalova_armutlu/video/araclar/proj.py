import numpy as np
KIYI = [(-183.64, -202.11), (-42.20, -149.82), (-6.23, -138.73), (19.17, -131.68),
        (47.72, -122.08), (65.04, -114.38), (70.62, -94.14), (78.85, -82.54),
        (99.55, -73.01), (128.77, -65.57), (151.13, -61.43), (172.57, -60.73)]
BLOK = []
for (u0, v0), (u1, v1), n, xb, yh in (((-22.36, 64.30), (-20.86, -71.76), 6, 12.92, 5.61),
                                     ((18.39, 63.37), (19.83, -54.54), 7, 11.67, 6.15)):
    for k in range(n):
        f = k / (n - 1)
        u, v = u0 + (u1 - u0) * f, v0 + (v1 - v0) * f
        for dx in (-xb, xb):
            for dy in (-yh, yh):
                for z in (0.0, 22.3):
                    BLOK.append((u + dx, v + dy, z))
TEKNE = {"iskele_tekne": (25.0, -150.0, 0.5), "yat": (112.0, -106.0, 0.5), "iskele_uc": (-27.6, -158.7, 0.3)}

def proj(C, T, lens, P, aspect=9 / 16):
    C, T = np.array(C, float), np.array(T, float)
    F = T - C; F /= np.linalg.norm(F)
    R = np.cross(F, [0, 0, 1.0]); R /= np.linalg.norm(R)
    U = np.cross(R, F)
    P = np.atleast_2d(np.array(P, float)) - C
    d = P @ F
    x = (P @ R) / d / (18.0 / lens)
    y = (P @ U) / d / (18.0 / lens * aspect)
    return np.stack([0.5 + x / 2, 0.5 + y / 2], 1)

def rapor(ad, C, T, lens):
    b = proj(C, T, lens, BLOK)
    k = proj(C, T, lens, [(u, v, 0) for u, v in KIYI])
    # kıyı çizgisinin kadraj içindeki kısmı
    ic = k[(k[:, 0] > 0) & (k[:, 0] < 1)]
    t = {n: proj(C, T, lens, [p])[0] for n, p in TEKNE.items()}
    print(f"{ad}: C={tuple(round(c,1) for c in C)} T={T} lens={lens}")
    print(f"   proje x {b[:,0].min():.2f}-{b[:,0].max():.2f}  y {b[:,1].min():.2f}-{b[:,1].max():.2f}  (genişlik {b[:,0].max()-b[:,0].min():.2f})")
    print(f"   kıyı (kadraj içi) y {ic[:,1].min():.2f}-{ic[:,1].max():.2f}" if len(ic) else "   kıyı kadraj dışı")
    print("   " + "  ".join(f"{n}=({p[0]:.2f},{p[1]:.2f})" for n, p in t.items()))

if __name__ == "__main__":
    C0, T0 = (138.0, -221.0, 70.0), (22.4, -46.0, 0.0)
    rapor("ORIJINAL", C0, T0, 35.0)
