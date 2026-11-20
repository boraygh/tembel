# -*- coding: utf-8 -*-
"""Müşteri etüdü (yalova_etüt 1–2, AutoCAD) – 7104 / 7105, zemin + 5 = 6 kat.

7104 (kuzeyden güneye): kuzey ucu boş; 2 standart blok (katta 4 adet 2+1, 288 m²), 2 büyük blok
(katta 8 adet 1+1, 380 m²), 1 standart blok, kıyıda geniş blok (katta 5 daire, iki çekirdek,
denize bakan balkon şeridi).
7105: kuzey ucu boş; 2 standart blok (katta 4 adet 2+1, uçlarda balkon), ortada büyük blok (katta
8 adet 1+1: köşelerde, kenar ortalarında), 2 standart blok.

Mimari önceki gibi (tp6_plan.py ile aynı yapıcılar); blok şekilleri ve yerleri etütten. Paftalar gerçek
kuzeye göre çizilmiş: parsel köşeleriyle benzerlik dönüşümü (ölçek 0,29 m/pt, dönme 17,7°, köşelerde
ortalama sapma 0,5 / 0,25 m). Standart bloklar 16blok.py blok tipiyle (uç balkonlu, giriş nişli);
büyük bloklarda balkon yerleri etütte çizilmediği için köşelere ve kenar ortalarına konuldu.

Kullanım: ns = runpy.run_path("yalova_armutlu_16blok.py", ...); etut_plan.uygula(ns); ns["kur"]()
"""
import tp6_plan as T

KAT_SAYISI = 6

# Standart: 16blok.py BLOK_TIPLERI anahtarları (bkz. _kontur); etütte oda bandı çıkıntısı yok (yu = yo).
C4 = dict(xb=13.05, xs=11.05, xr=7.20, yu=5.90, yo=5.90, nx=1.00, ny=3.80, oy=3.00,
          oda9=(3.50, 7.00), oda6=(1.20, 3.35), bk=11.75, brut=288.0, daire=4)       # 7104
D4 = dict(xb=12.15, xs=10.15, xr=6.60, yu=7.10, yo=7.10, nx=1.20, ny=4.60, oy=3.00,
          oda9=(3.40, 6.35), oda6=(1.45, 3.20), bk=10.85, brut=288.0, daire=4)       # 7105


def buyuk(hx, hy, b=2.1, kb=3.0, ob=1.6):
    """Katta 8 adet 1+1: dört köşe balkonu, uzun kenar ortalarında ikişer, kısa kenar ortalarında birer
    balkon olacak şekilde gövde hücreleri (balkonlar dış hatta oyulur). b: balkon derinliği, kb: köşe
    balkonu genişliği, ob: orta balkon yarı genişliği."""
    govde = [(-hx + b, hx - b, -hy + b, hy - b),
             (-hx + kb, -ob, hy - b, hy), (ob, hx - kb, hy - b, hy),
             (-hx + kb, -ob, -hy, -hy + b), (ob, hx - kb, -hy, -hy + b),
             (-hx, -hx + b, -hy + b, -ob), (-hx, -hx + b, ob, hy - b),
             (hx - b, hx, -hy + b, -ob), (hx - b, hx, ob, hy - b)]
    balkon = [(-hx, -hx + kb, hy - b, hy), (hx - kb, hx, hy - b, hy),
              (-hx, -hx + kb, -hy, -hy + b), (hx - kb, hx, -hy, -hy + b),
              (-ob, ob, hy - b, hy), (-ob, ob, -hy, -hy + b),
              (-hx, -hx + b, -ob, ob), (hx - b, hx, -ob, ob)]
    giris = ("y", hy, 1, -(hx - kb + ob) / 2)      # kuzeyde köşe ile orta balkon arasında
    return dict(tur="genel", daire=8, brut=380.0, govde=govde, balkon=balkon,
                kule=(-3.0, 3.0, -2.2, 2.2), giris=giris)


B8A = buyuk(13.10, 7.45)                          # 7104: 26,2 x 14,9 m
B8B = buyuk(11.65, 8.45)                          # 7105: 23,3 x 16,9 m
# Kıyı bloğu (7104 güneyi, 26,5 x 12,9 m): güneyde beş dairenin balkon şeridi, kuzeyde iki çekirdek.
S5 = dict(tur="genel", daire=5, brut=380.0,
          govde=[(-13.25, 13.25, -4.45, 6.45)],
          balkon=[(-13.25, -7.40, -6.45, -4.45), (-7.40, -2.00, -6.45, -4.45), (-2.00, 1.75, -6.45, -4.45),
                  (1.75, 7.25, -6.45, -4.45), (7.25, 13.25, -6.45, -4.45)],
          kule=[(-10.1, -4.9, 1.5, 5.5), (4.75, 9.75, 1.5, 5.5)], giris=("y", 6.45, 1, -7.5))

TIPLER = {"C4": C4, "D4": D4, "B8A": B8A, "B8B": B8B, "S5": S5}
# Blok merkezleri (u, v): etüt konturlarının ortası.
BLOKLAR = [
    ("7104", "C4", -22.45, 22.90), ("7104", "C4", -22.35, 5.40),
    ("7104", "B8A", -22.20, -13.55), ("7104", "B8A", -22.25, -34.20),
    ("7104", "C4", -22.30, -53.40), ("7104", "S5", -22.00, -71.75),
    ("7105", "D4", 19.30, 27.75), ("7105", "D4", 19.65, 7.85),
    ("7105", "B8B", 20.05, -12.95),
    ("7105", "D4", 20.20, -34.50), ("7105", "D4", 20.90, -53.90),
]


def rapor(bloklar):
    KAT = T.G["KAT"]
    print("\n============ YALOVA ARMUTLU – MÜŞTERİ ETÜDÜ (7104 / 7105) ============")
    top = [0, 0]
    for pid in ("7104", "7105"):
        bl = [b for b in bloklar if b["parsel"] == pid]
        say = {}
        for b in bl:
            say[b["tip"]] = say.get(b["tip"], 0) + 1
        daire = sum(TIPLER[b["tip"]]["daire"] for b in bl) * KAT
        top[0] += len(bl); top[1] += daire
        print(f"{pid}: {len(bl)} blok {say} | {daire} daire ({KAT} kat)")
    print(f"TOPLAM: {top[0]} blok | {top[1]} daire")
    print("=====================================================================\n")


# ------------------------------ arka (kuzey) uçlarda açık otopark ------------------------------
# Parsellerin deniz tarafında değil, kuzey uçlarındaki boş bahçede; giriş kuzeydeki yoldan, bahçe kapısından (u_m ± 3).
# Park yeri 2,5 x 5,0 m, manevra yolu 6,0 m; sıralar kuzey–güney, kuzey kenarda iki manevra yolunu bağlayan yol.
#   7104 (≈ 32 m genişlik): park | yol | park park | yol | park  -> 4 sıra x 13 = 52
#   7105 (≈ 27 m, doğu kenarı eğik): park | yol | park park | yol -> 3 sıra x 11 = 33
OTOPARK = {
    "7104": dict(x=(-38.3, -6.3), y=(33.0, 65.5), yol_y=(65.5, 71.5), kapi=-22.26, sirada=13,
                 seritler=[("park", -38.3, -33.3, -1), ("yol", -33.3, -27.3), ("park", -27.3, -22.3, 1),
                           ("park", -22.3, -17.3, -1), ("yol", -17.3, -11.3), ("park", -11.3, -6.3, 1)]),
    "7105": dict(x=(5.0, 32.0), y=(38.0, 65.5), yol_y=(65.5, 71.6), kapi=20.02, sirada=11,
                 seritler=[("park", 5.0, 10.0, -1), ("yol", 10.0, 16.0), ("park", 16.0, 21.0, 1),
                           ("park", 21.0, 26.0, -1), ("yol", 26.0, 32.0)]),
}
YOL_KUZEY_KENAR = 76.5                     # parsellerin kuzeyindeki yolun (v = 80,3, 7,6 m) güney kenarı
_ARAC = []                                 # kur() içindeki araba_tipleri sonucu (otopark araçları için)


def otopark_kutulari():
    """Mini plan için otopark alanları: [(x0, x1, y0, y1)]."""
    out = []
    for o in OTOPARK.values():
        out.append((o["x"][0], o["x"][1], o["y"][0], o["yol_y"][1]))
    return out


def park_yeri_sayisi():
    return sum(o["sirada"] * sum(1 for s in o["seritler"] if s[0] == "park") for o in OTOPARK.values())


def otopark(M, coll, agac_coll):
    import math, random
    G = T.G
    g = G["Govde"]()
    rnd = random.Random(G["TOHUM"] + 77)
    Z, CZ = 0.075, 0.08                    # asfalt üstü, çizgi üstü
    arac = 0
    for pid, o in OTOPARK.items():
        (x0, x1), (y0, y1), (cy0, cy1) = o["x"], o["y"], o["yol_y"]
        poly = G["P" + pid]
        # doğu kenarı eğik parselde manevra yolu kenara taşmasın
        xk = min(x1, G["_kenar_u"](poly, cy1, 1) - 1.4)
        g.kutu(x0, x1, y0, y1, 0.0, Z, M["asfalt"], alt=False)
        g.kutu(x0, xk, cy0, cy1, 0.0, Z, M["asfalt"], alt=False)
        # kapıdan kuzeydeki yola: bahçe duvarı / çit boşluğu (6 m) üstünden, kaldırımı kesen rampa
        kp = o["kapi"]
        g.kutu(kp - 3.0, kp + 3.0, cy1 - 0.1, YOL_KUZEY_KENAR + 0.3, 0.0, 0.16, M["asfalt"], alt=False)
        # blok tarafında taş yaya şeridi ve alçak çit (otoparkı bahçeden ayırır)
        g.kutu(x0, x1, y0 - 2.6, y0, 0.0, 0.06, M["tas"], alt=False)
        g.kutu(x0, x1, y0 - 0.45, y0 - 0.15, 0.0, 0.16, M["kaldirim"], alt=False)
        dy = (y1 - y0) / o["sirada"]
        for s in o["seritler"]:
            if s[0] != "park":
                continue
            _, a, b, burun = s                         # burun: -1 batıya, +1 doğuya (park yerinin dibine)
            dip = a if burun < 0 else b
            g.kutu(dip - 0.06, dip + 0.06, y0, y1, Z, CZ, M["cizgi"], alt=False)
            for k in range(o["sirada"] + 1):
                yy = y0 + k * dy
                g.kutu(a, b, yy - 0.06, yy + 0.06, Z, CZ, M["cizgi"], alt=False)
            for k in range(o["sirada"]):
                if rnd.random() > 0.8:
                    continue
                cx = (a + b) / 2 + burun * rnd.uniform(0.0, 0.25)
                cyy = y0 + (k + 0.5) * dy + rnd.uniform(-0.12, 0.12)
                yon = (0.0 if burun > 0 else math.pi) + (math.pi if rnd.random() < 0.2 else 0.0)
                G["ornekle"]("araba_otopark", rnd.choice(_ARAC), coll, (cx, cyy, Z - 0.04),
                             yon + rnd.uniform(-0.03, 0.03))
                arac += 1
        # manevra yolu orta çizgisi yok; kuzey yolda yön okları yerine kesik kenar çizgisi
        for xx in range(int(x0) + 1, int(xk) - 1, 3):
            g.kutu(xx, xx + 1.5, cy1 - 0.4, cy1 - 0.28, Z, CZ, M["cizgi"], alt=False)
    # otopark alanındaki bahçe ağaçlarını kaldır
    kutular = [(o["x"][0] - 1.0, o["x"][1] + 1.0, o["y"][0] - 0.8, o["yol_y"][1] + 1.0) for o in OTOPARK.values()]
    silinen = 0
    for ob in list(agac_coll.objects):
        ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
        if ic and ic.name.startswith("AGAC") and any(a <= ob.location.x <= b and c <= ob.location.y <= d
                                                    for a, b, c, d in kutular):
            G["bpy"].data.objects.remove(ob, do_unlink=True)
            silinen += 1
    print(f"otopark: {park_yeri_sayisi()} park yeri, {arac} araç, kaldırılan ağaç {silinen}", flush=True)
    return g.obje("OTOPARK", coll)


def uygula(ns):
    """16blok.py modül sözlüğünü etüde çevirir: tp6_plan'ın yapıcıları bu etüdün tipleri ve konumlarıyla."""
    gl = ns["kur"].__globals__
    gl["KAT"] = KAT_SAYISI
    T.TIPLER, T.BLOKLAR = TIPLER, BLOKLAR
    T.uygula(ns)
    gl["rapor"] = rapor
    T.G["rapor"] = rapor
    if OTOPARK_AC:
        tipler, peyzaj = gl["araba_tipleri"], gl["peyzaj"]

        def araba_tipleri(M, ust):
            _ARAC[:] = tipler(M, ust)
            return _ARAC

        def peyzaj_otoparkli(M, coll, bloklar, agac, agac_coll):
            ob = peyzaj(M, coll, bloklar, agac, agac_coll)
            otopark(M, coll, agac_coll)
            return ob
        gl["araba_tipleri"] = araba_tipleri
        gl["peyzaj"] = peyzaj_otoparkli


OTOPARK_AC = True                          # False: otoparksız ilk etüt sahnesi (yakın çekim renderları bununla)
