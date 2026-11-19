# -*- coding: utf-8 -*-
"""T_P-6 vaziyet planı (Katar Mühendislik Mimarlık, etüt çalışması) – 7104 / 7105, zemin + 4 kat.

7104 (kuzeyden güneye): 2 büyük blok (katta 8 adet 1+1, brüt 43 m²), 4 standart blok (katta 4 adet 2+1,
brüt 60 m²), kıyıda yan yana 2 küçük blok (katta 3 adet 2+1). 7105: 2 standart, 2 büyük, 2 standart blok.

Mimari önceki gibidir (traverten cephe, koyu kat silmeleri, yuvarlak köşeli balkonlar, çerçevesiz cam
korkuluk, bronz doğrama); yalnız blok şekilleri ve yerleri bu plandan gelir. Plan 1/500 PDF'ten ölçüldü:
parsel köşeleriyle benzerlik dönüşümü (ölçek 0,176 m/pt, dönme 0,6°, köşelerde ortalama sapma 0,4 m),
blok konturları kalın duvar çizgilerinden.

Standart bloklar T_P-4 bloğunun aynısıdır (16blok.py blok_tipi), ölçüler bu plana göre. Büyük ve küçük
bloklar plandaki oda ve balkon hücrelerinden kurulur: gövde hücrelerinin birleşimi duvarları, balkonlarla
birlikte birleşimi kat silmesini verir; balkonların dış köşeleri yuvarlatılır.

Kullanım: ns = runpy.run_path("yalova_armutlu_16blok.py", ...); tp6_plan.uygula(ns); ns["kur"]()
"""
import math
import random

# ------------------------------ blok tipleri (m) ------------------------------
# x: doğu +, y: kuzey + (denizden uzağa); blok merkezine göre.
# Standart: 16blok.py BLOK_TIPLERI ile aynı anahtarlar (bkz. _kontur); 7104 ve 7105'te genişlik farklı.
S7104 = dict(xb=12.65, xs=10.60, xr=7.00, yu=5.10, yo=6.10, nx=0.70, ny=3.20, oy=3.05,
             oda9=(3.30, 6.75), oda6=(0.90, 3.15), bk=11.30, brut=240.0, daire=4)
S7105 = dict(xb=11.55, xs=9.50, xr=6.30, yu=5.85, yo=6.20, nx=1.05, ny=3.20, oy=3.05,
             oda9=(3.35, 6.05), oda6=(1.30, 3.25), bk=10.05, brut=240.0, daire=4)
# Büyük blok: orta çekirdek (merdiven + 2 asansör) çevresinde 8 adet 1+1. Köşelerde dört, yanlarda iki,
# kuzey ve güney ortada birer balkon. Hücreler: (x0, x1, y0, y1).
B8 = dict(tur="genel", daire=8, brut=8 * 43.0,
          govde=[(-8.75, 8.66, -7.10, 7.30),                                  # orta gövde
                 (-8.75, -3.50, 7.30, 9.20), (-0.71, 8.66, 7.30, 9.20),       # kuzey bandı
                 (-8.75, -3.50, -9.00, -7.10), (-0.71, 8.66, -9.00, -7.10),   # güney bandı
                 (-10.31, -8.75, 3.50, 6.07), (-10.87, -8.75, -0.62, 3.50), (-10.31, -8.75, -5.87, -3.30),
                 (8.66, 10.22, 3.50, 6.07), (8.66, 10.78, -0.62, 3.50), (8.66, 10.22, -5.87, -3.30)],
          balkon=[(-11.34, -8.75, 6.07, 9.20), (8.66, 11.34, 6.07, 9.20),
                  (-11.34, -8.75, -9.00, -5.87), (8.66, 11.34, -9.00, -5.87),
                  (-11.23, -8.75, -3.30, -0.62), (8.66, 11.23, -3.30, -0.62),
                  (-3.50, -0.71, 7.30, 9.87), (-3.50, -0.71, -9.89, -7.10)],
          kule=(-3.6, 2.6, -2.6, 2.6), giris=None)
# Küçük blok (kıyıda ikiz): kuzeyde bir, güneyde denize bakan iki 2+1; dış yanda yan balkon, giriş iki
# blok arasındaki aralıktan. KL batıdaki (yan balkon batıda), KR onun aynası.
K3L = dict(tur="genel", daire=3, brut=3 * 60.0,
           govde=[(-4.88, 4.88, -7.88, 9.86)],
           balkon=[(-6.45, -4.88, 2.16, 8.62), (-4.88, 0.0, -9.86, -7.88), (0.0, 4.88, -9.86, -7.88)],
           kule=(-3.7, 4.4, 2.2, 5.4), giris=("x", 4.88, 1, 3.40))


def kuleler(t):
    """Çatı kuleleri: tek dikdörtgen ya da dikdörtgen listesi (birden çok çekirdekli bloklar)."""
    k = t["kule"]
    return [k] if isinstance(k[0], (int, float)) else list(k)


def _ayna(t):
    a = dict(t)
    for k in ("govde", "balkon"):
        a[k] = [(-x1, -x0, y0, y1) for x0, x1, y0, y1 in t[k]]
    a["kule"] = [(-x1, -x0, y0, y1) for x0, x1, y0, y1 in kuleler(t)]
    e, w, n, c = t["giris"]
    a["giris"] = (e, -w, -n, c)
    return a


K3R = _ayna(K3L)
TIPLER = {"S7104": S7104, "S7105": S7105, "B8": B8, "K3L": K3L, "K3R": K3R}

# Blok merkezleri (u, v): plandaki konturların ortası; küçük bloklarda gövdenin ortası (yan balkon hariç).
BLOKLAR = [
    ("7104", "B8", -22.10, 60.20), ("7104", "B8", -21.80, 33.10),
    ("7104", "S7104", -21.85, 9.40), ("7104", "S7104", -21.65, -9.10),
    ("7104", "S7104", -21.43, -27.60), ("7104", "S7104", -21.25, -46.12),
    ("7104", "K3L", -30.30, -69.03), ("7104", "K3R", -14.50, -68.85),
    ("7105", "S7105", 18.65, 63.97), ("7105", "S7105", 18.85, 44.38),
    ("7105", "B8", 19.40, 21.33), ("7105", "B8", 19.70, -9.23),
    ("7105", "S7105", 19.70, -34.00), ("7105", "S7105", 19.90, -53.95),
]

G = {}                                   # 16blok.py modül sözlüğü (uygula ile dolar)


# ------------------------------ geometri ------------------------------
def birlesim(rects):
    """Eksene paralel dikdörtgenlerin birleşiminin dış konturları (saat yönü tersine), ızgara yöntemiyle."""
    xs = sorted({round(v, 4) for r in rects for v in r[:2]})
    ys = sorted({round(v, 4) for r in rects for v in r[2:]})
    dolu = {(i, j) for i in range(len(xs) - 1) for j in range(len(ys) - 1)
            if any(r[0] <= (xs[i] + xs[i + 1]) / 2 <= r[1] and r[2] <= (ys[j] + ys[j + 1]) / 2 <= r[3]
                   for r in rects)}
    kenar = []
    for i, j in dolu:
        if (i, j - 1) not in dolu:
            kenar.append(((i, j), (i + 1, j)))
        if (i + 1, j) not in dolu:
            kenar.append(((i + 1, j), (i + 1, j + 1)))
        if (i, j + 1) not in dolu:
            kenar.append(((i + 1, j + 1), (i, j + 1)))
        if (i - 1, j) not in dolu:
            kenar.append(((i, j + 1), (i, j)))
    bas = {}
    for e in kenar:
        bas.setdefault(e[0], []).append(e)
    kullan, halkalar = set(), []
    for e in kenar:
        if e in kullan:
            continue
        halka, k = [], e
        while k not in kullan:
            kullan.add(k)
            halka.append(k[0])
            k = next((s for s in bas[k[1]] if s not in kullan), k)
        pts = [(xs[i], ys[j]) for i, j in halka]
        n = len(pts)
        pts = [p for m, p in enumerate(pts)
               if abs((p[0] - pts[m - 1][0]) * (pts[(m + 1) % n][1] - p[1]) -
                      (p[1] - pts[m - 1][1]) * (pts[(m + 1) % n][0] - p[0])) > 1e-9]
        if G["_alan"](pts) > 0:
            halkalar.append(pts)
    return halkalar


def _kose_mu(p, r):
    return any(abs(p[0] - x) < 1e-3 and abs(p[1] - y) < 1e-3 for x in r[:2] for y in r[2:])


def dis_kontur(t):
    """Balkonlar dahil taban konturu ve köşe başına yuvarlatma işareti (balkonların dış köşeleri)."""
    pts = max(birlesim(t["govde"] + t["balkon"]), key=lambda p: G["_alan"](p))
    n, yuv = len(pts), []
    for i, p in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        disbukey = (p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0]) > 0
        yuv.append(disbukey and any(_kose_mu(p, r) for r in t["balkon"]))
    return pts, yuv


def kontur_ofset(pts, yuv, o, r):
    """16blok._kontur'un ofset / yuvarlatma kısmı: işaretli dış köşeler r yarıçapla (komşu kenara
    sığacak kadar) yuvarlatılır, diğerleri gönye ile o kadar kaydırılır."""
    _sol_normal, _yay = G["_sol_normal"], G["_yay"]
    n, out = len(pts), []
    L = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]
    for i, (x, y) in enumerate(pts):
        n1 = _sol_normal((x, y), pts[i - 1])
        n2 = _sol_normal(pts[(i + 1) % n], (x, y))
        if yuv[i] and r > 0:
            rr = min(r, L[i - 1] * (0.48 if yuv[i - 1] else 0.95), L[i] * (0.48 if yuv[(i + 1) % n] else 0.95))
            a0 = math.degrees(math.atan2(n1[1], n1[0]))
            a1 = math.degrees(math.atan2(n2[1], n2[0]))
            out += _yay(x - rr * (n1[0] + n2[0]), y - rr * (n1[1] + n2[1]), rr + o, a0,
                        a1 + 360 if a1 < a0 else a1, 8)
        else:
            s = o / (1.0 + n1[0] * n2[0] + n1[1] * n2[1])
            out.append((x + s * (n1[0] + n2[0]), y + s * (n1[1] + n2[1])))
    return out


def _icinde(p, r, e=0.0):
    return r[0] - e < p[0] < r[1] + e and r[2] - e < p[1] < r[3] + e


def _kenarlar(pts):
    """Kontur kenarları: (eksen, w0, n, amin, amax); n dış normalin işareti (16blok._duvarlar ile aynı)."""
    for p, q in zip(pts, pts[1:] + pts[:1]):
        if abs(p[1] - q[1]) < 1e-6:
            yield "y", p[1], (1 if q[0] < p[0] else -1), *sorted((p[0], q[0]))
        else:
            yield "x", p[0], (1 if q[1] > p[1] else -1), *sorted((p[1], q[1]))


def _nokta(eksen, w, a):
    return (a, w) if eksen == "y" else (w, a)


# ------------------------------ büyük / küçük blok ------------------------------
def blok_tipi_genel(M, coll, ad, t):
    """Hücre tanımlı blok, 16blok.blok_tipi ile aynı mimari: bazalt kaide, koyu kat silmeleri (balkonların
    dış köşelerinde yuvarlak), traverten gövde, balkona sürgülü cam, cephede bronz kasalı pencereler ve
    salonlarda Fransız cam, arkalarında perdeli odalar; balkonlarda çerçevesiz cam korkuluk + bronz küpeşte,
    saksıda zeytin; çatıda saçak ve traverten merdiven kulesi."""
    g = G["Govde"]()
    KAT, KAT_H, Z0, DOSEME_T, SILME, R_KOSE = (G[k] for k in ("KAT", "KAT_H", "Z0", "DOSEME_T", "SILME", "R_KOSE"))
    DUVAR_T, ODA_PENCERE = G["DUVAR_T"], G["ODA_PENCERE"]
    Zc = Z0 + KAT * KAT_H
    Zt = Zc - DOSEME_T
    zk = Z0 + KAT_H
    rnd = random.Random(G["TOHUM"] + len(ad) * 7 + int(kuleler(t)[0][0] * 10))
    F, yuv = dis_kontur(t)
    govde = birlesim(t["govde"])
    balkon = t["balkon"]

    g.prizma(kontur_ofset(F, yuv, 0.30, R_KOSE), 0.0, Z0, M["kaide"], ust=M["tas"], alt=False)
    for i in range(1, KAT):
        z = Z0 + i * KAT_H
        g.prizma(kontur_ofset(F, yuv, SILME, R_KOSE), z - DOSEME_T, z, M["silme"], ust=M["tas"], alt=M["ahsap"])
    g.prizma(kontur_ofset(F, yuv, SILME + 0.15, R_KOSE), Zt, Zc + 0.25, M["silme"], ust=M["cati"], alt=M["ahsap"])
    for x0, x1, y0, y1 in kuleler(t):                 # merdiven / asansör kuleleri
        g.kutu(x0, x1, y0, y1, Zc + 0.25, Zc + 2.9, M["traverten"], alt=False)
        g.kutu(x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, Zc + 2.9, Zc + 3.1, M["silme"], alt=M["ahsap"])
        g.kutu(x0 + 0.8, x0 + 1.9, y1 - 0.02, y1 + 0.03, Zc + 0.29, Zc + 2.45, M["antrasit"])

    # balkonlar: korkuluk hattı kat silmesinin 7 cm içinden, balkonun dış kenarları boyunca
    ray = kontur_ofset(F, yuv, SILME - 0.07, R_KOSE)
    hatlar = []
    for r in balkon:
        yakin = [_icinde(p, r, SILME + 0.02) for p in ray]
        if all(yakin):
            hatlar.append(ray + ray[:1])
            continue
        s = yakin.index(False)
        dizi, parca = ray[s:] + ray[:s], []
        for p, y in zip(dizi, yakin[s:] + yakin[:s]):
            if y:
                parca.append(p)
            elif parca:
                if len(parca) > 1:
                    hatlar.append(parca)
                parca = []
        if len(parca) > 1:
            hatlar.append(parca)
    bolme = [(a, b) for k, a in enumerate(balkon) for b in balkon[k + 1:]
             if (abs(a[1] - b[0]) < 1e-3 or abs(b[1] - a[0]) < 1e-3) and min(a[3], b[3]) - max(a[2], b[2]) > 0.5]
    for i in range(KAT):
        z = Z0 + i * KAT_H
        z1 = z + KAT_H - DOSEME_T
        for h in hatlar:
            g.serit(h, z, z + 1.05, 0.024, M["korkuluk"])
            g.serit(h, z + 1.05, z + 1.085, 0.05, M["bronz"])
        for a, b in bolme:
            x = a[1] if abs(a[1] - b[0]) < 1e-3 else a[0]
            ya, yb = max(a[2], b[2]), min(a[3], b[3])
            g.kutu(x - 0.09, x + 0.09, ya, yb, z, z1, M["traverten"])
        for r in balkon:                                  # gövdeye yakın köşede saksıda zeytin
            cx, cy = (r[0] + r[1]) / 2, (r[2] + r[3]) / 2
            px = r[0] + 0.45 if abs(r[0]) < abs(r[1]) else r[1] - 0.45
            py = r[2] + 0.45 if abs(r[2]) < abs(r[3]) else r[3] - 0.45
            if abs(r[1] - r[0]) < 1.2 or abs(r[3] - r[2]) < 1.2:
                px, py = cx, cy
            g.silindir((px, py, z), (px, py, z + 0.55), 0.28, M["antrasit"], 10)
            g.silindir((px, py, z + 0.55), (px, py, z + 1.15), 0.04, M["ahsap"], 6)
            g.kure((px, py, z + 1.45), (0.50, 0.48, 0.40), M["zeytin"], 10, 6, 0.25, i * 1.7 + px + py * 0.4)

    # katlar: kenarlar balkon sınırlarında bölünür; balkona bakan parça sürgülü cam, dış parça pencere
    kesit = sorted({v for r in balkon for v in r})
    pw, ph, pp = ODA_PENCERE
    for i in range(KAT):
        zf = Z0 + i * KAT_H
        zt = zf + KAT_H - DOSEME_T
        ac = []
        for halka in govde:
            for eksen, w0, n, amin, amax in _kenarlar(halka):
                sinir = [amin] + [v for v in kesit if amin + 0.05 < v < amax - 0.05] + [amax]
                for s0, s1 in zip(sinir, sinir[1:]):
                    L = s1 - s0
                    disari = _nokta(eksen, w0 + n * 0.05, (s0 + s1) / 2)
                    balkona = any(_icinde(disari, r) for r in balkon)
                    temas = any(_icinde(_nokta(eksen, w0 + n * 0.05, a), r, 0.06) for r in balkon for a in (s0, s1))
                    ortak = dict(eksen=eksen, w0=w0, n=n, z0=zf, z1=zt)
                    giris = t["giris"]
                    if (i == 0 and giris and giris[0] == eksen and abs(giris[1] - w0) < 1e-3 and
                            giris[2] == n and s0 + 1.0 < giris[3] < s1 - 1.0):
                        ac.append(dict(ortak, a0=giris[3] - 0.85, a1=giris[3] + 0.85, tur="giris"))
                        continue
                    if balkona:
                        if L >= 1.6:
                            c, w = (s0 + s1) / 2, min(L - 0.7, 3.0)
                            ac.append(dict(ortak, a0=c - w / 2, a1=c + w / 2, tur="surme",
                                           acik=rnd.choice((0.0, 0.0, 0.0, 0.45, 0.85))))
                    elif L >= 2.0:
                        if temas and L >= 3.0:          # balkon yanındaki salon: Fransız cam balkon ucunda
                            w = min(L - 1.2, 2.6)
                            uc = s0 if any(_icinde(_nokta(eksen, w0 + n * 0.05, s0), r, 0.06) for r in balkon) else s1
                            c = uc + (0.6 + w / 2) * (1 if uc == s0 else -1)
                            ac.append(dict(ortak, a0=c - w / 2, a1=c + w / 2, tur="pencere", dikme=2,
                                           fransiz=i > 0))
                            s0, s1 = (c + w / 2 + 0.3, s1) if uc == s0 else (s0, c - w / 2 - 0.3)
                            L = s1 - s0
                        k = round(L / 3.0)
                        for m in range(k if L / max(k, 1) >= 2.0 else 0):
                            c = s0 + L * (m + 0.5) / k
                            ac.append(dict(ortak, a0=c - pw / 2, a1=c + pw / 2, z0=zf + pp, z1=zf + pp + ph,
                                           tur="pencere", dikme=1))
        for halka in govde:
            _duvarlar_genel(g, M, halka, ac, zf, zt)
        for k, a in enumerate(ac):
            args = (g, M, a["eksen"], a["w0"], a["n"], a["a0"], a["a1"], a["z0"], a["z1"])
            if a["tur"] == "surme":
                G["_surme"](*args, a["acik"])
            elif a["tur"] == "giris":
                G["_giris"](*args)
            else:
                G["_pencere"](*args, a["dikme"])
            if a.get("fransiz"):
                G["_fransiz"](g, M, a["eksen"], a["w0"], a["n"], a["a0"], a["a1"], zf)
            # açıklığın arkasında oda: zemin, tavan, iç duvarlar, perde; ışık oda başına değişir
            rid = 1.0 + i * 40 + k
            ic0, ic1 = a["w0"] - a["n"] * DUVAR_T, a["w0"] - a["n"] * (DUVAR_T + 2.8)
            w0_, w1_ = sorted((ic0, ic1))
            b0, b1 = a["a0"] - 0.3, a["a1"] + 0.3
            r = (b0, b1, w0_, w1_) if a["eksen"] == "y" else (w0_, w1_, b0, b1)
            yon = ("+" if a["n"] > 0 else "-") + a["eksen"]
            g.ozellik(oda=rid)
            G["_oda_kabugu"](g, M, r, {yon}, zf, zt)
            if a["tur"] != "giris":
                G["_perde"](g, M, a, rid, 0, zf, zt)
            g.ozellik()

    # bina girişi: sahanlık, basamaklar, tik altlı saçak
    if t["giris"]:
        eksen, w0, n, c = t["giris"]
        def kutu(w_a, w_b, a0, a1, z0, z1, mat, **kw):
            wa, wb = sorted((w0 + n * w_a, w0 + n * w_b))
            if eksen == "y":
                g.kutu(a0, a1, wa, wb, z0, z1, mat, **kw)
            else:
                g.kutu(wa, wb, a0, a1, z0, z1, mat, **kw)
        kutu(0.0, 1.6, c - 1.3, c + 1.3, 0.0, Z0 - 0.005, M["kaide"], ust=M["tas"])
        for k in range(3):
            kutu(1.6 + 0.35 * k, 1.95 + 0.35 * k, c - 1.7, c + 1.7, 0.0, Z0 - 0.15 * (k + 1), M["kaide"], ust=M["tas"])
        kutu(0.0, 1.9, c - 1.6, c + 1.6, zk - DOSEME_T + 0.01, zk - 0.01, M["silme"], alt=M["ahsap"])
    return g.obje(ad, coll)


def _duvarlar_genel(g, M, pts, aciklik, zf, zt):
    """16blok._duvarlar'ın genel konturlu hâli: açıklıklar dışındaki duvar parçaları, dış yüz traverten."""
    for eksen, w0, n, amin, amax in _kenarlar(pts):
        bu = sorted((a for a in aciklik if a["eksen"] == eksen and abs(a["w0"] - w0) < 1e-6 and
                     a["n"] == n and amin - 1e-6 <= a["a0"] and a["a1"] <= amax + 1e-6), key=lambda a: a["a0"])
        imlec = amin
        for a in bu:
            if a["a0"] > imlec + 1e-6:
                G["_duvar_kutu"](g, eksen, w0, n, imlec, a["a0"], zf, zt, M["traverten"], M["ic_siva"])
            if a["z0"] > zf + 1e-6:
                G["_duvar_kutu"](g, eksen, w0, n, a["a0"], a["a1"], zf, a["z0"], M["traverten"], M["ic_siva"],
                                 ust=M["traverten"])
            if a["z1"] < zt - 1e-6:
                G["_duvar_kutu"](g, eksen, w0, n, a["a0"], a["a1"], a["z1"], zt, M["traverten"], M["ic_siva"],
                                 alt=M["traverten"])
            imlec = a["a1"]
        if amax > imlec + 1e-6:
            G["_duvar_kutu"](g, eksen, w0, n, imlec, amax, zf, zt, M["traverten"], M["ic_siva"])


# ------------------------------ yerleşim, peyzaj, rapor ------------------------------
def yerlesim():
    out, say = [], {}
    for pid, tip, u, v in BLOKLAR:
        k = say[pid] = say.get(pid, -1) + 1
        out.append(dict(ad=f"{pid}-{chr(65 + k)}", parsel=pid, tip=tip, u=u, v=v))
    return out


def kapsam(t):
    """Blok taban kutusu (balkonlar dahil): x0, x1, y0, y1."""
    if t.get("tur") == "genel":
        r = t["govde"] + t["balkon"]
        return min(a[0] for a in r), max(a[1] for a in r), min(a[2] for a in r), max(a[3] for a in r)
    return -t["xb"], t["xb"], -max(t["yu"], t["yo"]), max(t["yu"], t["yo"])


def peyzaj(M, coll, bloklar, agac, agac_coll):
    """16blok.peyzaj'ın karma blok dizisine uyarlanmış hâli: çim, bahçe duvarı + çit, blok çevresi taş
    döşeme, iki yanda yürüyüş yolu, kuzey / güney kapı aksları, bloklar arası zeytin, yanlarda servi."""
    g = G["Govde"]()
    rnd = random.Random(G["TOHUM"] + 5)
    R_KOSE, ornekle = G["R_KOSE"], G["ornekle"]

    def agac_koy(tip, u, v, olcek=1.0):
        ornekle(tip.lower(), agac[tip], agac_coll, (u, v, 0.04), rnd.uniform(0, 6.28), olcek * rnd.uniform(0.9, 1.1))

    for pid, poly in (("7104", G["P7104"]), ("7105", G["P7105"])):
        bl = sorted((b for b in bloklar if b["parsel"] == pid), key=lambda b: -b["v"])
        dizi = [b for b in bl if not b["tip"].startswith("K")]
        ikiz = [b for b in bl if b["tip"].startswith("K")]
        u_m = sum(b["u"] for b in dizi) / len(dizi)
        kapilar = (("kuzey", u_m, 6.0), ("guney", u_m, 4.0))
        g.prizma(poly, 0.0, 0.04, M["cim"], alt=False)
        for p in G["_kenar_parcalari"](poly, 0.15, kapilar):
            g.serit(p, 0.0, 0.55, 0.25, M["beyaz"])
        for p in G["_kenar_parcalari"](poly, 0.95, kapilar):
            g.serit(p, 0.0, 1.25, 0.8, M["yesil"])
        vk, vg = G["_kenar_v"](poly, u_m, 1), G["_kenar_v"](poly, u_m, -1)
        vt = vk - 1.6
        kap = {id(b): kapsam(TIPLER[b["tip"]]) for b in bl}
        B = max(max(-kap[id(b)][0], kap[id(b)][1]) for b in dizi)
        alt_ucu = (max(b["v"] + kap[id(b)][3] for b in ikiz) + 1.6) if ikiz else vg + 1.6
        # iki yanda yürüyüş yolu (küçük blokların kuzeyinde biter) + kuzey / güney bağlantıları
        for sx in (-1, 1):
            w = u_m + sx * (B + 1.05)
            g.kutu(w - 0.75, w + 0.75, alt_ucu, vt, 0.0, 0.05, M["tas"], alt=False)
        for vv, yon in ((vt, -1), (alt_ucu, 1)):
            g.kutu(u_m - B - 1.8, u_m + B + 1.8, *sorted((vv, vv + yon * 1.5)), 0.0, 0.05, M["tas"], alt=False)
        g.kutu(u_m - 1.5, u_m + 1.5, vt, vk - 0.1, 0.0, 0.05, M["tas"], alt=False)
        b0 = bl[0]
        g.kutu(u_m - 1.5, u_m + 1.5, b0["v"] + kap[id(b0)][3] + 1.0, vt, 0.0, 0.05, M["tas"], alt=False)
        g.kutu(u_m - 1.2, u_m + 1.2, vg + 0.1, alt_ucu, 0.0, 0.05, M["tas"], alt=False)
        # blok çevresi taş döşeme
        for b in bl:
            t = TIPLER[b["tip"]]
            if t.get("tur") == "genel":
                x0, x1, y0, y1 = kap[id(b)]
                g.kutu(b["u"] + x0 - 1.3, b["u"] + x1 + 1.3, b["v"] + y0 - 1.3, b["v"] + y1 + 1.3,
                       0.0, 0.055, M["tas"], alt=False)
            else:
                g.prizma([(b["u"] + x, b["v"] + y) for x, y in G["_kontur"](t, True, 1.3, R_KOSE, nis=False)],
                         0.0, 0.055, M["tas"], alt=False)
        # bloklar arası: dar geçit taş, genişte iki zeytin; yanlarda yer varsa servi
        for a, b in zip(dizi, dizi[1:]):
            ust, alt_ = a["v"] + kap[id(a)][2], b["v"] + kap[id(b)][3]
            vm, bos = (ust + alt_) / 2, ust - alt_
            if bos < 4.5:
                g.kutu(u_m - B - 1.8, u_m + B + 1.8, vm - bos / 2, vm + bos / 2, 0.0, 0.052, M["tas"], alt=False)
            else:
                for du in (-6.0, 6.0):
                    agac_koy("AGAC_ZEYTIN", u_m + du, vm, 0.75)
            for sx in (-1, 1):
                yol = u_m + sx * (B + 1.8)
                cit = G["_kenar_u"](poly, vm, sx) - sx * 1.35
                if sx * (cit - yol) >= 1.5:
                    agac_koy("AGAC_SERVI", (yol + cit) / 2, vm, min(1.0, sx * (cit - yol) / 2.2) * 0.9)
        # standart blokların girişinin iki yanında küçük zeytin
        for b in dizi:
            t = TIPLER[b["tip"]]
            if t.get("tur") != "genel":
                for sx in (-1, 1):
                    agac_koy("AGAC_ZEYTIN", b["u"] + sx * 2.6, b["v"] + max(t["yu"], t["yo"]) + 2.3, 0.6)
        # kuzey bahçe: zeytin; küçük blokların arası taş avlu, kıyı tarafında palmiye
        for du in (-9.0, 9.0):
            agac_koy("AGAC_ZEYTIN", u_m + du, (vt + b0["v"] + kap[id(b0)][3] + 1.3) / 2, 0.85)
        if ikiz:
            ua = max(b["u"] + kap[id(b)][1] for b in ikiz if b["u"] < u_m)
            ub = min(b["u"] + kap[id(b)][0] for b in ikiz if b["u"] > u_m)
            vy = min(b["v"] + kap[id(b)][2] for b in ikiz)
            g.kutu(ua + 0.3, ub - 0.3, vy - 0.5, alt_ucu, 0.0, 0.056, M["tas"], alt=False)
            for vv in (vy + 3.0, vy + 9.0):
                agac_koy("AGAC_PALMIYE", (ua + ub) / 2, vv, 0.8)
        else:
            vs = (vg + 1.6 + bl[-1]["v"] + kap[id(bl[-1])][2] - 1.3) / 2
            for du in (-11.5, -5.0, 5.0, 11.5):
                agac_koy("AGAC_PALMIYE", u_m + du, vs, 0.9)
    return g.obje("PEYZAJ", coll)


def rapor(bloklar):
    KAT = G["KAT"]
    arsa = {"7104": 5648.0, "7105": 4510.0}
    print("\n================ YALOVA ARMUTLU – T_P-6 (7104 / 7105) ================")
    top = [0, 0, 0.0]
    for pid in ("7104", "7105"):
        bl = [b for b in bloklar if b["parsel"] == pid]
        say = {}
        for b in bl:
            say[b["tip"]] = say.get(b["tip"], 0) + 1
        daire = sum(TIPLER[b["tip"]]["daire"] for b in bl) * KAT
        brut = sum(TIPLER[b["tip"]]["brut"] for b in bl) * KAT
        top[0] += len(bl); top[1] += daire; top[2] += brut
        print(f"{pid}: {len(bl)} blok {say} | {daire} daire | daire brütü {brut:,.0f} m² | ≈ {brut / arsa[pid]:.2f} × arsa")
    print(f"TOPLAM: {top[0]} blok | {top[1]} daire | daire brütü {top[2]:,.0f} m²")
    print("=====================================================================\n")


def uygula(ns):
    """16blok.py modül sözlüğünde blok tiplerini, yerleşimi, peyzajı ve raporu T_P-6'ya çevirir."""
    gl = ns["kur"].__globals__
    eski = gl["blok_tipi"]

    def blok_tipi(M, coll, ad, t):
        return blok_tipi_genel(M, coll, ad, t) if t.get("tur") == "genel" else eski(M, coll, ad, t)

    gl["BLOK_TIPLERI"] = TIPLER
    gl["blok_tipi"] = blok_tipi
    gl["yerlesim"] = yerlesim
    gl["peyzaj"] = peyzaj
    gl["rapor"] = rapor
    G.clear()
    G.update(gl)
