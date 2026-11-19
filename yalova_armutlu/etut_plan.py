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


def uygula(ns):
    """16blok.py modül sözlüğünü etüde çevirir: tp6_plan'ın yapıcıları bu etüdün tipleri ve konumlarıyla."""
    gl = ns["kur"].__globals__
    gl["KAT"] = KAT_SAYISI
    T.TIPLER, T.BLOKLAR = TIPLER, BLOKLAR
    T.uygula(ns)
    gl["rapor"] = rapor
    T.G["rapor"] = rapor
