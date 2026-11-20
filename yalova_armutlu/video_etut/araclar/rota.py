# Müşteri etüdü videosunun kamera rotası (8 + 7 videosunun rota.py'si, etut_plan.py yerleşimine uyarlandı;
# saf Python: Blender ve kaplama betiği aynı rotayı kullanır). Bloklar 6 katlı.
#   1 yaklaşma   denizden gelen drone iki parselin arasındaki yoldan geçip sol sıranın en arkadaki bloğunun
#                köşesine varır, denize döner
#   2 kayma      en üst kat köşelerinden (göz 17,7 m) arkadan öne ağır ağır; her balkonda yavaşlar
#   3 panorama   kıyı bloğunun denize bakan balkon köşesinde doğudan batıya tarama (ilk 8,2 sn önceki sürümle aynı)
#   4 yükseliş   yaya hizasına inmeden: bloktan uzaklaşıp ortadaki yolun üstüne, 40 m'ye; bütün siteyi yukarıdan görür
#   5 genişlik   ortadan ileri, ~33 m: önce sola 5. ve 7. blok, sonra sağa 6. blok (1+1, katta 8 daire)
#   6 otopark    arkaya: iki parselin kuzey ucundaki otoparkların üstüne, yere bakarak yerinde 180° döner
#   7 deniz      arkadan denize doğru siteyi baştan sona geçip sahilin üstünde durur
# kareler() her kare için dict(x, y, z, h, p, bolum, blok) döner. h: pusula yönü (0 = kuzey, 90 = doğu), p: eğim (°).
# blok: vurgulanan blok numarası, numara demeti ya da None.
import json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(D, "..", ".."))
import etut_plan

FPS = 24
GOZ = 0.60 + (etut_plan.KAT_SAYISI - 1) * 3.10 + 1.6          # en üst kat göz hizası (17,7 m)


def _kose(tip, u, v):
    """Blok balkonunun güneydoğu (sokak + deniz tarafı) köşesinin 1,6 m dışı."""
    x0, x1, y0, y1 = etut_plan.T.kapsam(etut_plan.TIPLER[tip])
    return (u + x1 + 1.6, v + y0, GOZ)


SOL = sorted((b for b in etut_plan.BLOKLAR if b[0] == "7104"), key=lambda b: -b[3])
SAG = sorted((b for b in etut_plan.BLOKLAR if b[0] == "7105"), key=lambda b: -b[3])
DURAK = [_kose(t, u, v) for _, t, u, v in SOL]                  # sol sıra en arka ... en ön
# blok numaraları: denize en yakından başlayarak sol 1, sağ 2, sol 3, sağ 4 ... (sol tek, sağ çift)
HARF = [2 * (len(SOL) - i) - 1 for i in range(len(SOL))]       # sol sıra, en arkadan en öne: 11 ... 1
NO_SAG = [2 * (len(SAG) - i) for i in range(len(SAG))]         # sağ sıra, en arkadan en öne: 10 ... 2
BLOK_V = [v for _, _, _, v in SOL]                              # sol sıra blok merkezleri (y)
BLOK_YD = [(lambda k: (k[3] - k[2]) / 2)(etut_plan.T.kapsam(etut_plan.TIPLER[t])) for _, t, _, _ in SOL]
H_KAYMA, P_KAYMA = 177.0, -7.0
YURU_X = -3.4      # önceki sürümün yürüyüş hattı: bu hattaki sokak araçları / ağaçları kaldırılmış kalır (yeniden
                   # kullanılan kayma ve panorama kareleri yeni karelerle aynı sahneden olsun)


def yumusak(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (6 * x - 15) + 10)


def hermite(noktalar, tegetler=None):
    """[(t, deger_listesi)] -> f(t): zamana göre teğetli kübik Hermite (C1), uçlarda hız sıfır.
    tegetler: {anahtar no: [teğet ya da None (otomatik)]} -- dönüş noktalarında sıfır hız, ek yerinde süreklilik."""
    n = len(noktalar)
    T = [p[0] for p in noktalar]
    P = [p[1] for p in noktalar]
    m = []
    for i in range(n):
        if i == 0 or i == n - 1:
            m.append([0.0] * len(P[i]))
        else:
            m.append([(P[i + 1][k] - P[i - 1][k]) / (T[i + 1] - T[i - 1]) for k in range(len(P[i]))])
        for k, v in enumerate((tegetler or {}).get(i, [])):
            if v is not None:
                m[i][k] = v

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
    Q = [(0.0, [34.0, -330.0, 61.0, yon(-34.6, 250.0) - 360.0, -11.0]),     # yönler sürekli (sarmasız)
         (4.0, [8.0, -190.0, 33.0, -2.0, -7.0]),
         (7.0, [-0.6, -95.0, 21.0, 0.0, -4.0]),
         (12.5, [-0.6, A[1] - 22.0, 19.1, 0.0, -3.0]),
         (14.6, [-2.4, A[1] - 5.0, 18.5, 70.0, -5.0]),
         (16.4, [A[0], A[1], A[2], H_KAYMA, P_KAYMA])]
    f1 = hermite(Q)
    T1 = 16.4
    ekle(int(T1 * FPS), lambda t: (*f1(t)[:5], HARF[0] if t > T1 - 0.6 else None), "yaklasma")
    ekle(int(0.8 * FPS), lambda t: (A[0], A[1], A[2], H_KAYMA, P_KAYMA, HARF[0]), "kayma")

    # ---- 2 kayma: A → H, balkon hizalarında yavaşlayarak (hız 3,5 … 10 m/s), uçlarda yumuşak kalkış/duruş ----
    L = math.dist(DURAK[0][:2], DURAK[-1][:2])
    seg = L / (len(DURAK) - 1)
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
        blok = HARF[min(int(s / seg + 0.5), len(DURAK) - 1)]
        return x, y, DURAK[0][2], H_KAYMA, P_KAYMA, blok
    ekle(int(T2 * FPS) + 1, kayma, "kayma")

    # ---- 3 panorama: H'de doğudan batıya (ilk 8,2 sn önceki sürümle kare kare aynı; batıda kalkışa devreder) ----
    Hd = DURAK[-1]
    pan = hermite([(0.0, [H_KAYMA, P_KAYMA]), (0.5, [H_KAYMA, P_KAYMA]), (3.0, [112.0, -5.0]),
                   (8.2, [238.0, -5.0]), (10.6, [H_KAYMA, P_KAYMA]), (11.0, [H_KAYMA, P_KAYMA])])
    TP = 8.2
    npan = int(TP * FPS) + 1                                   # t <= 8,2 sn olan kareler
    ekle(npan, lambda t: (Hd[0], Hd[1], Hd[2], *pan(t), HARF[-1]), "panorama")
    h_tg = (H_KAYMA - 112.0) / (10.6 - 3.0)                   # eski eğrinin 8,2 sn'deki teğetleri
    p_tg = (P_KAYMA + 5.0) / (10.6 - 3.0)

    # ---- 4–7: yaya hizasına inmeden yukarıdan: ortadan kalkış, 1+1 büyük bloklar, arkada otopark, denize dönüş ----
    Kx = [(0.0, [Hd[0], Hd[1], Hd[2], 238.0, -5.0]),
          (2.3, [-3.6, -84.5, 29.0, 276.0, -13.0]),            # bloktan uzaklaşıp yükselirken sağa döner
          (5.0, [-0.3, -96.0, 40.0, 360.0, -28.0]),            # ortadan, yukarıdan bütün site (geri çekilip durur)
          (8.8, [-0.6, -70.0, 33.0, 333.0, -24.0]),            # 5. ve 7. blok (1+1, katta 8 daire)
          (12.6, [-2.5, -46.0, 34.0, 395.0, -28.0]),           # 6. blok (1+1, katta 8 daire)
          (17.0, [-0.3, 20.0, 46.0, 360.0, -44.0]),            # arkaya: iki otopark önde
          (21.5, [-0.3, 50.0, 50.0, 368.0, -58.0]),            # otoparkların üstünde, yere bakarak
          (28.0, [-0.3, 64.0, 52.0, 540.0, -50.0]),            # yerinde döner, denize bakar
          (34.8, [-0.3, -28.0, 38.0, 540.0, -22.0]),
          (41.5, [-0.3, -92.0, 27.0, 540.0, -15.0])]           # arkadan denize, sahilin üstünde durur
    teg = {0: [0.0, 0.0, 0.0, h_tg, p_tg],
           2: [0.0, 0.0, None, None, None],                     # geri çekilmeden ileriye: durur
           5: [None, None, None, 0.0, None],                    # sola bakıştan sağa dönüşe
           6: [None, None, None, 6.0, None],                    # dönüş otoparkın üstünde yavaş başlar
           7: [0.0, 0.0, None, 0.0, None]}                      # kuzeye süzülüşten güneye uçuşa, dönüş biter
    f4 = hermite(Kx, teg)
    T4 = Kx[-1][0]

    def ust(t):
        x, y, z, h, p = f4(t)
        if 7.0 <= t < 11.0:
            bl, bo = (5, 7), "genislik"
        elif 11.0 <= t < 15.0:
            bl, bo = 6, "genislik"
        elif 15.0 <= t < 29.0:
            bl, bo = None, "otopark"
        else:
            bl, bo = None, ("yukselis" if t < 15.0 else "deniz")
        return x, y, z, h, p, (bl, bo)
    for i in range(int(T4 * FPS) + 1):
        t = (i + npan) / FPS - TP                              # panoramanın zamanından devam
        x, y, z, h, p, (bl, bo) = ust(t)
        out.append(dict(x=x, y=y, z=z, h=h % 360.0, p=p, bolum=bo, blok=bl))
    yf = out[-1]
    ekle(int(1.5 * FPS), lambda t: (yf["x"], yf["y"], yf["z"], yf["h"], yf["p"], None), "deniz")
    return out


if __name__ == "__main__":
    k = kareler()
    from collections import Counter
    print(len(k), "kare", f"{len(k) / FPS:.1f} sn", Counter(x["bolum"] for x in k))
    for i in range(0, len(k), 48):
        q = k[i]
        print(f"{i / FPS:6.1f} sn  {q['bolum']:9s} x {q['x']:7.1f} y {q['y']:7.1f} z {q['z']:5.1f} h {q['h']:6.1f} p {q['p']:5.1f} {q['blok']}")
