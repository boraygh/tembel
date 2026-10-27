# Önizleme videosunun kamera rotası (saf Python; Blender ve kaplama betiği aynı rotayı kullanır).
#   1 yaklaşma   denizden gelen drone iki parselin arasındaki yoldan geçip A bloğun köşesine varır, denize döner
#   2 kayma      en üst kat köşelerinden (göz 14,6 m) A'dan H'ye ağır ağır; her balkonda yavaşlar
#   3 panorama   H'de doğudan batıya tarama
#   4 dönüş      hızla A'ya geri, yaya hizasına iner
#   5 yürüyüş    yaya hizasında (göz 1,7 m) biraz daha hızlı, iki parselin arasındaki yoldan sahile
# kareler() her kare için dict(x, y, z, h, p, bolum, blok) döner. h: pusula yönü (0 = kuzey, 90 = doğu), p: eğim (°).
import json, math, os

D = os.path.dirname(os.path.abspath(__file__))
FPS = 24
K = json.load(open(os.path.join(D, "kameralar87.json")))
DURAK = [tuple(K[f"S{i}"]["konum"]) for i in range(1, 9)]          # sol sıra en arka ... en ön, z = 14,6
# blok numaraları: denize en yakından başlayarak sol 1, sağ 2, sol 3, sağ 4 ... (sol tek, sağ çift)
HARF = [15, 13, 11, 9, 7, 5, 3, 1]                                  # sol sıra, en arkadan en öne
NO_SAG = [14, 12, 10, 8, 6, 4, 2]                                   # sağ sıra, en arkadan en öne
BLOK_V = [64.3 - i * (64.3 + 71.76) / 7 for i in range(8)]          # sol sıra blok merkezleri (y)
H_KAYMA, P_KAYMA = 177.0, -7.0
YURU_X, GOZ_YAYA = -3.4, 1.7
YURU_Y0, YURU_Y1 = 61.0, -90.0


def zemin(y):
    """Yürüyüş hattında zemin yüksekliği (Blender'ın ışın taramasından, yoksa 0,3 m)."""
    yol = os.path.join(D, "zemin.json")
    if not hasattr(zemin, "tablo"):
        zemin.tablo = json.load(open(yol)) if os.path.exists(yol) else None
    t = zemin.tablo
    if not t:
        return 0.3
    ys, zs = t["y"], t["z"]
    if y >= ys[0]:
        return zs[0]
    for i in range(1, len(ys)):
        if y >= ys[i]:
            f = (y - ys[i - 1]) / (ys[i] - ys[i - 1])
            return zs[i - 1] + (zs[i] - zs[i - 1]) * f
    return zs[-1]


def yumusak(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def hermite(noktalar):
    """[(t, deger_listesi)] -> f(t): zamana göre teğetli kübik Hermite (C1), uçlarda hız sıfır."""
    n = len(noktalar)
    T = [p[0] for p in noktalar]
    P = [p[1] for p in noktalar]
    m = []
    for i in range(n):
        if i == 0 or i == n - 1:
            m.append([0.0] * len(P[i]))
        else:
            m.append([(P[i + 1][k] - P[i - 1][k]) / (T[i + 1] - T[i - 1]) for k in range(len(P[i]))])

    def f(t):
        t = min(max(t, T[0]), T[-1])
        i = max(j for j in range(n - 1) if T[j] <= t)
        h = T[i + 1] - T[i]
        s = (t - T[i]) / h
        h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
        return [h00 * P[i][k] + h10 * h * m[i][k] + h01 * P[i + 1][k] + h11 * h * m[i + 1][k] for k in range(len(P[i]))]
    return f


def yon(dx, dy):
    return math.degrees(math.atan2(dx, dy)) % 360.0


def kareler():
    out = []
    t0 = 0.0

    def ekle(n, fn, bolum):
        for i in range(n):
            x, y, z, h, p, blok = fn(i / FPS)
            out.append(dict(x=x, y=y, z=z, h=h % 360.0, p=p, bolum=bolum, blok=blok))

    # ---- 1 yaklaşma: denizden, iki parselin arasındaki yoldan A'ya ----
    A = DURAK[0]
    Q = [(0.0, [34.0, -330.0, 58.0, yon(-34.6, 250.0) - 360.0, -11.0]),     # yönler sürekli (sarmasız)
         (4.0, [8.0, -190.0, 30.0, -2.0, -7.0]),
         (7.0, [-0.6, -95.0, 18.0, 0.0, -4.0]),
         (12.5, [-0.6, 32.0, 16.0, 0.0, -3.0]),
         (14.6, [-2.4, 54.0, 15.4, 70.0, -5.0]),
         (16.4, [A[0], A[1], A[2], H_KAYMA, P_KAYMA])]
    f1 = hermite(Q)
    T1 = 16.4
    ekle(int(T1 * FPS), lambda t: (*f1(t)[:5], HARF[0] if t > T1 - 0.6 else None), "yaklasma")
    ekle(int(0.8 * FPS), lambda t: (A[0], A[1], A[2], H_KAYMA, P_KAYMA, HARF[0]), "kayma")

    # ---- 2 kayma: A → H, balkon hizalarında yavaşlayarak (hız 3,5 … 10 m/s), uçlarda yumuşak kalkış/duruş ----
    L = math.dist(DURAK[0][:2], DURAK[-1][:2])
    seg = L / 7
    a, b = 3.5, 6.5
    s, t, dt, izler = 0.0, 0.0, 1.0 / 240, []
    while s < L:
        v = a + b * math.sin(math.pi * (s % seg) / seg) ** 2
        v *= max(0.08, yumusak(t / 1.2))                      # kalkış
        kalan = L - s
        v = min(v, max(0.25, math.sqrt(2 * 1.6 * kalan)))     # H'de yumuşak duruş (yavaşlama 1,6 m/s²)
        s += v * dt
        t += dt
        izler.append((t, min(s, L)))
    T2 = izler[-1][0]

    def kayma(tt):
        i = min(int(tt / dt), len(izler) - 1)
        s = izler[i][1]
        f = s / L
        x = DURAK[0][0] + (DURAK[-1][0] - DURAK[0][0]) * f
        y = DURAK[0][1] + (DURAK[-1][1] - DURAK[0][1]) * f
        blok = HARF[min(int(s / seg + 0.5), 7)]
        return x, y, DURAK[0][2], H_KAYMA, P_KAYMA, blok
    ekle(int(T2 * FPS) + 1, kayma, "kayma")

    # ---- 3 panorama: H'de doğudan batıya ----
    Hd = DURAK[-1]
    pan = hermite([(0.0, [H_KAYMA, P_KAYMA]), (0.5, [H_KAYMA, P_KAYMA]), (3.0, [112.0, -5.0]),
                   (8.2, [238.0, -5.0]), (10.6, [H_KAYMA, P_KAYMA]), (11.0, [H_KAYMA, P_KAYMA])])
    ekle(int(11.0 * FPS), lambda t: (Hd[0], Hd[1], Hd[2], *pan(t), HARF[7]), "panorama")

    # ---- 4 dönüş: hızla A'ya, sonunda yaya hizasına iner ----
    zy0 = zemin(YURU_Y0) + GOZ_YAYA
    T4 = 4.2

    def donus(t):
        u = yumusak(t / T4)
        x = Hd[0] + (YURU_X - Hd[0]) * u
        y = Hd[1] + (YURU_Y0 - Hd[1]) * u
        z = Hd[2] + (zy0 - Hd[2]) * yumusak((u - 0.5) / 0.5)
        h = H_KAYMA + (yon(0.02, -1.0) - H_KAYMA) * u
        p = P_KAYMA + (0.0 - P_KAYMA) * yumusak((u - 0.5) / 0.5)
        return x, y, z, h, p, None
    ekle(int(T4 * FPS), donus, "donus")
    ekle(int(0.5 * FPS), lambda t: (YURU_X, YURU_Y0, zy0, yon(0.02, -1.0), 0.0, None), "yuruyus")

    # ---- 5 yürüyüş: yaya hizasında A'dan sahile, ~7,5 m/s; hafif adım salınımı ----
    Ly = YURU_Y0 - YURU_Y1
    vmax, s, t, izler = 7.5, 0.0, 0.0, []
    while s < Ly:
        v = vmax * max(0.06, yumusak(t / 1.2))
        v = min(v, max(0.2, math.sqrt(2 * 2.2 * (Ly - s))))
        s += v * dt
        t += dt
        izler.append((t, min(s, Ly), v))
    T5 = izler[-1][0]

    def yuru(tt):
        i = min(int(tt / dt), len(izler) - 1)
        _, s, v = izler[i]
        y = YURU_Y0 - s
        sal = 0.018 * (v / vmax) * math.sin(2 * math.pi * 1.9 * tt)
        blok = None
        for j, bv in enumerate(BLOK_V):
            if abs(y - bv) < 9.7:
                blok = HARF[j]
        return YURU_X, y, zemin(y) + GOZ_YAYA + sal, yon(0.02, -1.0), 0.0, blok
    ekle(int(T5 * FPS) + 1, yuru, "yuruyus")
    yf = out[-1]
    ekle(int(1.6 * FPS), lambda t: (yf["x"], yf["y"], yf["z"], yf["h"], yf["p"], None), "yuruyus")
    return out


if __name__ == "__main__":
    k = kareler()
    from collections import Counter
    print(len(k), "kare", f"{len(k) / FPS:.1f} sn", Counter(x["bolum"] for x in k))
    for i in range(0, len(k), 48):
        q = k[i]
        print(f"{i / FPS:6.1f} sn  {q['bolum']:9s} x {q['x']:7.1f} y {q['y']:7.1f} z {q['z']:5.1f} h {q['h']:6.1f} p {q['p']:5.1f} {q['blok']}")
