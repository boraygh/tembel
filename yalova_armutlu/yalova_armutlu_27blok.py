# -*- coding: utf-8 -*-
"""
YALOVA · ARMUTLU · KARŞIYAKA MAH. (Tavşantepe Mevkii, Pafta 39/2)
PARSEL 7104 (5.648 m²) + 7105 (4.510 m²)
27 BLOK · ZEMİN+5 = 6 KAT · KATTA 2 DAİRE  ->  324 DAİRE        (v2 · fotogerçekçi)

Blender 4.2 – 5.x · Cycles (GPU önerilir)
Arayüzden : Scripting sekmesi > Open > bu dosya > Run Script
            İki sahne kurulur: "YALOVA_GENEL" (tüm proje) ve "YALOVA_TEK_BLOK" -> F12
Konsoldan : blender -b -P yalova_armutlu_27blok.py -- --render  [--cikti KLASOR] [--ornek N]
            [--cevrimdisi]  (internet kullanmadan, prosedürel malzemelerle)

İlk çalıştırmada Poly Haven'dan (CC0, ücretsiz) altın saat gökyüzü HDRI'ı ve PBR dokular
indirilir (~60 MB, bir kez; ~/Yalova_Armutlu_Render/polyhaven altında saklanır).
İnternet yoksa script prosedürel malzemelerle devam eder.

Parsel köşeleri TKGM parsel sorgusundan, kıyı/yollar uydu görüntüsünden ölçeklendi.
Koordinat sistemi parsel eksenine hizalı: +Y = parsel boyu (denizden uzağa), deniz -Y yönünde.
Gerçek kuzey bu eksenin 17° batısında; güneş buna göre hesaplanıyor.
"""
import bpy
import gc
import json
import math
import os
import random
import shutil
import sys
import urllib.request

import numpy as np
from mathutils import Matrix, Vector, kdtree, noise

# ============================== AYARLAR ==============================
CIKTI_KLASORU = os.path.join(os.path.expanduser("~"), "Yalova_Armutlu_Render")
VARLIK_KLASORU = os.path.join(os.path.expanduser("~"), "Yalova_Armutlu_Render", "polyhaven")
OTOMATIK_RENDER = False          # True -> iki PNG'yi render alıp CIKTI_KLASORU'na yazar
ORNEK = 384                      # Cycles sample (GPU'da 384-512 rahat)
COZ_GENEL = (2560, 1440)         # tüm proje
COZ_BLOK = (1600, 2000)          # tek blok (4:5 dikey)
GUNES_AZIMUT = 222.0             # derece, kuzeyden saat yönünde (222 = GB, ikindi güneşi)
GUNES_YUKSEKLIK = 18.0           # yalnız yedek gökyüzünde; HDRI'da güneş yüksekliği görüntüden gelir
GUNES_TONU = (1.0, 0.86, 0.70)   # altın saat sıcaklığı
GOK_TONU = (1.0, 0.95, 0.88)
HEDEF_GUNES = 5.0                # güneş ışınımı (sahne ölçeği)
POZLAMA = 0.9
TOHUM = 11

POLYHAVEN = True                 # False -> internet kullanma, tamamen prosedürel
HDRI = "syferfontein_18d_clear_puresky"
HDRI_COZ = "4k"
DOKU_COZ = "2k"
DOKULAR = {                      # Poly Haven doku kimlikleri (CC0)
    "kiremit": "clay_roof_tiles_02",
    "asfalt": "aerial_asphalt_01",
    "kumsal": "aerial_beach_01",
    "arazi": "aerial_grass_rock",
    "cim": "leafy_grass",
    "siva": "white_stucco",
    "tas": "rectangular_paving",
}

# Atmosfer: uzak mesafe pusu (altın saat)
PUS_RENK, PUS_GUC = "#F0DDB8", 0.78
PUS_BAS, PUS_SON, PUS_MAKS = 230.0, 2600.0, 0.66
ORMAN_YOGUNLUK = 0.016           # tepelerde ağaç / m²

# Blok ölçüleri (m)
B_W, B_D = 10.0, 10.5            # gövde: parsel enine x parsel boyuna
KAT, KAT_H = 6, 3.10             # zemin + 5 normal kat, kattan kata
Z0 = 0.60                        # zemin kat döşeme kotu (+0.60)
DOSEME_T = 0.30                  # döşeme alnı
TERAS_D = 1.70                   # denize bakan teras
DONUS_W, DONUS_L = 1.00, 3.20    # köşe terasın yan cepheye dönüşü
R_KOSE = 1.10                    # teras köşe yarıçapı
CEK_W, CEK_C = 3.0, 0.50         # merdiven+asansör çekirdeği, kuzeye çıkma

# Çekme mesafeleri (krokideki 3,5 – 5)
CEKME_YAN, CEKME_ON = 3.5, 5.0
CIKMA_ON = 1.5                   # açık çıkma (teras) ön bahçeye taşabilir

_ARG = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--render" in _ARG:
    OTOMATIK_RENDER = True
if "--onizleme" in _ARG:
    ORNEK, COZ_GENEL, COZ_BLOK = 24, (960, 540), (480, 600)
if "--cikti" in _ARG:
    CIKTI_KLASORU = _ARG[_ARG.index("--cikti") + 1]
if "--ornek" in _ARG:
    ORNEK = int(_ARG[_ARG.index("--ornek") + 1])
if "--cevrimdisi" in _ARG:
    POLYHAVEN = False

# =========================== PALET (sRGB HEX) ===========================
# Sancaktepe'de kullandığınız kodlar varsa bu satırlara birebir yazın; tüm sahne günceller.
PALET = {
    "beyaz":       "#ECE8E1",   # döşeme alınları, yüzer saçak – sıcak beyaz kompozit
    "traverten":   "#CDBDA2",   # cephe kaplama – açık traverten
    "antrasit":    "#2C2E31",   # çekirdek kulesi, saksılar
    "kaide":       "#3D3A36",   # zemin kaidesi – bazalt
    "bronz":       "#8E6C49",   # doğrama, dikey fin, küpeşte – şampanya bronz
    "ahsap":       "#7B4A2B",   # teras tavanları, saçak altı – tik
    "cam":         "#24323A",   # cephe camı – füme
    "perde":       "#DED5C4",   # cam arkası tül perde
    "korkuluk":    "#E4F2EE",   # çerçevesiz cam korkuluk
    "tas":         "#D9D1C3",   # teras / peyzaj taşı
    "minder":      "#EEEAE3",   # şezlong minderi
    "yesil":       "#4C6B2E",   # çit, saksı bitkisi
    "cati_yesil":  "#6E7F3C",   # yeşil çatı (sedum)
    "cim":         "#6F8F3A",
    "havuz":       "#5EC8D2",
    "deniz_kiyi":  "#5DBFB4",
    "deniz_sig":   "#1E8A92",
    "deniz_derin": "#0D3F5C",
    "deniz_yosun": "#244F45",
    "kum":         "#C9B795",
    "asfalt":      "#4A4B4D",
    "kaldirim":    "#B8B3AA",
    "cizgi":       "#ECEBE6",
    "ev_duvar":    "#DDD5C6",
    "ev_cati":     "#B3573A",   # mevcut yazlıklar – kiremit
    "gunes_panel": "#1B2433",   # güneş enerjili su ısıtıcı paneli
    "tank":        "#E8E8E4",
    "demir":       "#2F3032",
    "metal":       "#5C5F62",
    "arazi":       "#8A8A55",
    "orman":       "#34492A",
    "yaprak":      "#3F5C2A",
    "zeytin":      "#7A8A63",
    "cam_yaprak":  "#2F4726",
    "palmiye":     "#4E6B2C",
    "govde":       "#5A4634",
    "ten":         "#C69A7C",
}

# ===================== SAHA VERİSİ (parsel ekseninde, m) =====================
P7104 = [(-4.57, 72.91), (-6.02, 74.79), (-38.89, 75.20), (-39.86, 72.58),
         (-40.44, -82.01), (-4.01, -82.50)]
P7105 = [(3.43, -66.29), (38.40, -64.90), (33.16, 73.98), (5.47, 74.81), (3.37, 73.01)]
KIYI = [(-183.64, -202.11), (-42.20, -149.82), (-6.23, -138.73), (19.17, -131.68),
        (47.72, -122.08), (65.04, -114.38), (70.62, -94.14), (78.85, -82.54),
        (99.55, -73.01), (128.77, -65.57), (151.13, -61.43), (172.57, -60.73),
        (194.86, -75.52), (213.35, -84.39), (228.76, -76.88), (241.95, -62.17),
        (257.05, -47.27), (287.96, -44.04), (425.62, -6.31)]
SAHIL_YOLU = [(-133.57, -172.88), (-51.08, -121.05), (-21.15, -103.15), (3.39, -86.91),
              (50.00, -66.00), (91.36, -40.08), (123.20, -21.99), (164.48, -2.56)]
ZAFER_CD = [(-309.65, 272.79), (-69.19, 200.51), (98.37, 151.36), (234.53, 140.11),
            (401.99, 109.28), (559.29, 142.10)]
ISKELELER = [((-31.63, -145.77), (-27.64, -158.72)), ((15.35, -132.07), (20.23, -147.90)),
             ((215.79, -82.06), (221.33, -100.05))]
KUZEY_SAPMA = 16.98              # gerçek kuzeyin +Y'ye göre açısı (derece, batıya)

DOKU = {}                        # indirilen dokular: anahtar -> {"diff","rough","disp"}


# ============================== YARDIMCILAR ==============================
def renk(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _kat(c, f):
    return tuple(min(1.0, max(0.0, x * f)) for x in c)


def smooth(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def sahneyi_temizle():
    sc = bpy.context.scene
    for s in list(bpy.data.scenes):
        if s != sc:
            bpy.data.scenes.remove(s)
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for ng in list(bpy.data.node_groups):
        if ng.name.startswith("YALOVA_"):
            bpy.data.node_groups.remove(ng)
    for coll in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights, bpy.data.materials,
                 bpy.data.worlds):
        for b in list(coll):
            if b.users == 0:
                coll.remove(b)
    return sc


def koleksiyon(ad, ust=None):
    c = bpy.data.collections.new(ad)
    (ust or bpy.context.scene.collection).children.link(c)
    return c


def ornekle(ad, kaynak, coll, loc, rot=0.0, olcek=1.0):
    e = bpy.data.objects.new(ad, None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = kaynak
    e.empty_display_size = 2.0
    e.location = loc
    e.rotation_euler = (0.0, 0.0, rot)
    e.scale = (olcek, olcek, olcek)
    coll.objects.link(e)
    return e


# ---------------------------- Poly Haven (CC0) ----------------------------
def _ph_ac(url, zaman=40):
    req = urllib.request.Request(url, headers={"User-Agent": "yalova-blender-script/2.0"})
    try:
        return urllib.request.urlopen(req, timeout=zaman)
    except Exception as e:
        if "CERTIFICATE" not in str(e).upper():
            raise
        import ssl
        import certifi                     # bazı Blender kurulumlarında sistem sertifikası yok
        return urllib.request.urlopen(req, timeout=zaman,
                                      context=ssl.create_default_context(cafile=certifi.where()))


def _ph_indir(url, hedef):
    if os.path.exists(hedef) and os.path.getsize(hedef) > 0:
        return hedef
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with _ph_ac(url, 240) as r, open(hedef + ".part", "wb") as f:
        shutil.copyfileobj(r, f)
    os.replace(hedef + ".part", hedef)
    return hedef


def ph_doku(asset):
    klasor = os.path.join(VARLIK_KLASORU, asset)
    hedef = {k: os.path.join(klasor, f"{asset}_{k}_{DOKU_COZ}.jpg") for k in ("diff", "rough", "disp")}
    if all(os.path.exists(p) for p in hedef.values()):
        return hedef
    if not POLYHAVEN:
        return None
    try:
        with _ph_ac("https://api.polyhaven.com/files/" + asset) as r:
            files = json.loads(r.read().decode("utf-8"))
        for k, anahtar in (("diff", "Diffuse"), ("rough", "Rough"), ("disp", "Displacement")):
            _ph_indir(files[anahtar][DOKU_COZ]["jpg"]["url"], hedef[k])
        print("  Poly Haven doku:", asset)
        return hedef
    except Exception as e:
        print("  Poly Haven indirilemedi, prosedürel devam:", asset, "-", e)
        return None


def ph_hdri():
    hedef = os.path.join(VARLIK_KLASORU, HDRI, f"{HDRI}_{HDRI_COZ}.hdr")
    if os.path.exists(hedef):
        return hedef
    if not POLYHAVEN:
        return None
    try:
        with _ph_ac("https://api.polyhaven.com/files/" + HDRI) as r:
            files = json.loads(r.read().decode("utf-8"))
        _ph_indir(files["hdri"][HDRI_COZ]["hdr"]["url"], hedef)
        print("  Poly Haven HDRI:", HDRI)
        return hedef
    except Exception as e:
        print("  HDRI indirilemedi, prosedürel gökyüzü:", e)
        return None


def dokulari_hazirla():
    DOKU.clear()
    for anahtar, asset in DOKULAR.items():
        d = ph_doku(asset)
        if d:
            DOKU[anahtar] = d


# ---------------------------- geometri ----------------------------
def _sol_normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l = math.hypot(dx, dy) or 1.0
    return (-dy / l, dx / l)


def _ofset(pts, h):
    n = len(pts)
    L, R = [], []
    for i in range(n):
        if i == 0:
            nx, ny = _sol_normal(pts[0], pts[1]); k = 1.0
        elif i == n - 1:
            nx, ny = _sol_normal(pts[-2], pts[-1]); k = 1.0
        else:
            n1, n2 = _sol_normal(pts[i - 1], pts[i]), _sol_normal(pts[i], pts[i + 1])
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            l = math.hypot(mx, my) or 1.0
            nx, ny = mx / l, my / l
            k = 1.0 / max(0.35, nx * n1[0] + ny * n1[1])
        x, y = pts[i]
        L.append((x + nx * h * k, y + ny * h * k))
        R.append((x - nx * h * k, y - ny * h * k))
    return L, R


def _alan(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
                     poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def _yay(cx, cy, r, a0, a1, seg=10):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / seg)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / seg))) for k in range(seg + 1)]


def _cizgi_boyunca(pts, adim):
    """Çizgi boyunca eşit aralıklı (nokta, birim teğet) listesi."""
    out = []
    kalan = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        t = (dx / L, dy / L)
        s = kalan
        while s < L:
            out.append(((a[0] + t[0] * s, a[1] + t[1] * s), t))
            s += adim
        kalan = s - L
    return out


class Govde:
    """Basit mesh toplayıcı: kutu / prizma / şerit / silindir -> tek obje, malzeme slotlu."""

    def __init__(self):
        self.v, self.f, self.m, self.mats = [], [], [], []
        self.ton = []            # köşe başına renk tonu (komşu evler için)
        self._t = 0.0

    def _mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _v(self, pts):
        self.v += pts
        self.ton += [self._t] * len(pts)

    def yuz(self, idx, mat):
        self.f.append(tuple(idx))
        self.m.append(self._mi(mat))

    def prizma(self, poly, z0, z1, yan, ust=None, alt=None):
        if _alan(poly) < 0:
            poly = poly[::-1]
        n, b = len(poly), len(self.v)
        self._v([(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly])
        for i in range(n):
            j = (i + 1) % n
            self.yuz((b + i, b + j, b + n + j, b + n + i), yan)
        if ust is not False:
            self.yuz([b + n + i for i in range(n)], ust or yan)
        if alt is not False:
            self.yuz([b + i for i in reversed(range(n))], alt or yan)

    def kutu(self, x0, x1, y0, y1, z0, z1, mat, ust=None, alt=None):
        self.prizma([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, mat, ust, alt)

    def kutu_m(self, merkez, yarim, R, mat):
        """Yönlendirilmiş kutu: merkez, yarı boyutlar, 3x3 dönüş matrisi."""
        b = len(self.v)
        pts = []
        for i in range(8):
            p = R @ Vector(((1 if i & 1 else -1) * yarim[0], (1 if i & 2 else -1) * yarim[1],
                            (1 if i & 4 else -1) * yarim[2]))
            pts.append((merkez[0] + p.x, merkez[1] + p.y, merkez[2] + p.z))
        self._v(pts)
        for q in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
            self.yuz([b + i for i in q], mat)

    def silindir(self, p0, p1, r, mat, seg=10):
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0).normalized()
        yuk = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
        a = d.cross(yuk).normalized()
        bb = d.cross(a)
        b = len(self.v)
        halka = [(a * math.cos(2 * math.pi * j / seg) + bb * math.sin(2 * math.pi * j / seg)) * r
                 for j in range(seg)]
        self._v([tuple(p0 + o) for o in halka] + [tuple(p1 + o) for o in halka])
        for j in range(seg):
            j2 = (j + 1) % seg
            self.yuz((b + j, b + j2, b + seg + j2, b + seg + j), mat)
        self.yuz([b + j for j in reversed(range(seg))], mat)
        self.yuz([b + seg + j for j in range(seg)], mat)

    def koni(self, cx, cy, z0, z1, r, mat, seg=10):
        b = len(self.v)
        self._v([(cx + r * math.cos(2 * math.pi * j / seg), cy + r * math.sin(2 * math.pi * j / seg), z0)
                 for j in range(seg)] + [(cx, cy, z1)])
        for j in range(seg):
            self.yuz((b + j, b + (j + 1) % seg, b + seg), mat)
        self.yuz([b + j for j in reversed(range(seg))], mat)

    def profil(self, pts_xz, y0, y1, mat):
        """XZ düzlemindeki profili Y boyunca uzatır (araç gövdesi vb.)."""
        if _alan(pts_xz) < 0:
            pts_xz = pts_xz[::-1]
        n, b = len(pts_xz), len(self.v)
        self._v([(x, y0, z) for x, z in pts_xz] + [(x, y1, z) for x, z in pts_xz])
        self.yuz([b + i for i in range(n)], mat)
        self.yuz([b + n + i for i in reversed(range(n))], mat)
        for i in range(n):
            j = (i + 1) % n
            self.yuz((b + i, b + n + i, b + n + j, b + j), mat)

    def serit(self, pts, z0, z1, t, mat, ust=None):
        """Açık çizgi boyunca düşey ince kütle (cam korkuluk, çit, duvar, kaldırım)."""
        L, R = _ofset(pts, t / 2.0)
        b = len(self.v)
        for (lx, ly), (rx, ry) in zip(L, R):
            self._v([(lx, ly, z0), (lx, ly, z1), (rx, ry, z0), (rx, ry, z1)])
        for i in range(len(pts) - 1):
            a = b + 4 * i
            self.yuz((a, a + 1, a + 5, a + 4), mat)
            self.yuz((a + 2, a + 6, a + 7, a + 3), mat)
            self.yuz((a + 1, a + 3, a + 7, a + 5), ust or mat)
            self.yuz((a, a + 4, a + 6, a + 2), mat)
        self.yuz((b, b + 2, b + 3, b + 1), mat)
        e = b + 4 * (len(pts) - 1)
        self.yuz((e, e + 1, e + 3, e + 2), mat)

    def yatay_serit(self, pts, gen, z, mat):
        L, R = _ofset(pts, gen / 2.0)
        b = len(self.v)
        for (lx, ly), (rx, ry) in zip(L, R):
            self._v([(lx, ly, z), (rx, ry, z)])
        for i in range(len(pts) - 1):
            a = b + 2 * i
            self.yuz((a + 1, a + 3, a + 2, a), mat)

    def kure(self, c, r, mat, seg=12, hal=8, puruz=0.0, tohum=0.0):
        cx, cy, cz = c
        rx, ry, rz = r
        b = len(self.v)
        pts = [(cx, cy, cz + rz)]
        for i in range(1, hal):
            th = math.pi * i / hal
            for j in range(seg):
                ph = 2 * math.pi * j / seg
                d = (math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th))
                k = 1.0 + puruz * noise.noise(Vector((d[0] * 1.7 + tohum, d[1] * 1.7, d[2] * 1.7)))
                pts.append((cx + rx * d[0] * k, cy + ry * d[1] * k, cz + rz * d[2] * k))
        pts.append((cx, cy, cz - rz))
        self._v(pts)
        top, bot = b, b + 1 + (hal - 1) * seg
        for j in range(seg):
            j2 = (j + 1) % seg
            self.yuz((top, b + 1 + j, b + 1 + j2), mat)
            for i in range(hal - 2):
                r0, r1 = b + 1 + i * seg, b + 1 + (i + 1) * seg
                self.yuz((r0 + j, r1 + j, r1 + j2, r0 + j2), mat)
            rl = b + 1 + (hal - 2) * seg
            self.yuz((bot, rl + j2, rl + j), mat)

    def kirma_cati(self, x0, x1, y0, y1, z, h, mat, tasma=0.45):
        x0 -= tasma; x1 += tasma; y0 -= tasma; y1 += tasma
        w, d = x1 - x0, y1 - y0
        b = len(self.v)
        if w >= d:
            r, ym = d / 2, (y0 + y1) / 2
            self._v([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
                     (x0 + r, ym, z + h), (x1 - r, ym, z + h)])
            for q in ((0, 1, 5, 4), (1, 2, 5), (2, 3, 4, 5), (3, 0, 4), (0, 3, 2, 1)):
                self.yuz([b + i for i in q], mat)
        else:
            r, xm = w / 2, (x0 + x1) / 2
            self._v([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z),
                     (xm, y0 + r, z + h), (xm, y1 - r, z + h)])
            for q in ((1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5), (0, 1, 4), (0, 3, 2, 1)):
                self.yuz([b + i for i in q], mat)

    def obje(self, ad, coll, ton_attr=False):
        me = bpy.data.meshes.new(ad)
        me.from_pydata(self.v, [], self.f)
        for mt in self.mats:
            me.materials.append(mt)
        me.polygons.foreach_set("material_index", self.m)
        if ton_attr:
            a = me.attributes.new("ton", 'FLOAT', 'POINT')
            a.data.foreach_set("value", self.ton)
        me.update()
        ob = bpy.data.objects.new(ad, me)
        coll.objects.link(ob)
        return ob


# ============================== MALZEMELER ==============================
def _yeni_mat(ad):
    m = bpy.data.materials.new(ad)
    if m.node_tree is None:
        m.use_nodes = True
    try:                                  # pus/pencere emisyonu ışık kaynağı sayılmasın
        m.cycles.emission_sampling = 'NONE'
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out


def _ata(node, deger, *adlar):
    for a in adlar:
        s = node.inputs.get(a)
        if s is not None:
            try:
                s.default_value = deger
            except Exception:
                pass
            return s
    return None


def _bsdf(nt, rgb, rough=0.5, metal=0.0, spec=0.5, coat=0.0, trans=0.0, ior=1.45):
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _ata(p, (*rgb, 1.0), "Base Color")
    _ata(p, rough, "Roughness")
    _ata(p, metal, "Metallic")
    _ata(p, spec, "Specular IOR Level", "Specular")
    _ata(p, coat, "Coat Weight", "Coat", "Clearcoat")
    _ata(p, 0.02, "Coat Roughness", "Clearcoat Roughness")
    _ata(p, trans, "Transmission Weight", "Transmission")
    _ata(p, ior, "IOR")
    return p


def _koord(nt, tip="Object"):
    if tip == "Position":
        return nt.nodes.new("ShaderNodeNewGeometry").outputs["Position"]
    return nt.nodes.new("ShaderNodeTexCoord").outputs[tip]


def _gurultu(nt, vec, olcek, detay=6.0, w=None):
    nz = nt.nodes.new("ShaderNodeTexNoise")
    if w is not None:
        nz.noise_dimensions = '4D'
        nt.links.new(w, nz.inputs["W"])
    _ata(nz, olcek, "Scale")
    _ata(nz, detay, "Detail")
    _ata(nz, 0.55, "Roughness")
    nt.links.new(vec, nz.inputs["Vector"])
    return nz.outputs["Fac"]


def _rampa(nt, fac, duraklar):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    el[1].position, el[1].color = duraklar[-1][0], (*duraklar[-1][1], 1.0)
    el[0].position, el[0].color = duraklar[0][0], (*duraklar[0][1], 1.0)
    for pos, c in duraklar[1:-1]:
        e = el.new(pos)
        e.color = (*c, 1.0)
    nt.links.new(fac, r.inputs["Fac"])
    return r.outputs["Color"]


def _karistir(nt, fac, a, b):
    """Renk karıştır (ShaderNodeMix / RGBA) – a,b soket ya da rgb tuple."""
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = 'RGBA'
    f = [s for s in mx.inputs if s.name == "Factor" and s.type == 'VALUE'][0]
    A = [s for s in mx.inputs if s.name == "A" and s.type == 'RGBA'][0]
    B = [s for s in mx.inputs if s.name == "B" and s.type == 'RGBA'][0]
    for sok, val in ((A, a), (B, b)):
        if isinstance(val, tuple):
            sok.default_value = (*val, 1.0)
        else:
            nt.links.new(val, sok)
    if isinstance(fac, float):
        f.default_value = fac
    else:
        nt.links.new(fac, f)
    return [s for s in mx.outputs if s.type == 'RGBA'][0]


def _matematik(nt, op, a, b=None, c=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _vmat(nt, op, a, b=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, tuple):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _olcekle(nt, vec, s):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = 'SCALE'
    nt.links.new(vec, n.inputs[0])
    if isinstance(s, (int, float)):
        n.inputs["Scale"].default_value = s
    else:
        nt.links.new(s, n.inputs["Scale"])
    return n.outputs[0]


def _aralik(nt, deger, a0, a1, b0, b1):
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    mr.inputs[1].default_value, mr.inputs[2].default_value = a0, a1
    mr.inputs[3].default_value, mr.inputs[4].default_value = b0, b1
    nt.links.new(deger, mr.inputs[0])
    return mr.outputs[0]


def _bump(nt, p, yuk, guc=0.2, mesafe=0.05):
    b = nt.nodes.new("ShaderNodeBump")
    _ata(b, guc, "Strength")
    _ata(b, mesafe, "Distance")
    nt.links.new(yuk, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])


def _golge_seffaf(nt, out, shader):
    """Gölge ışınlarında saydam (cam/su gölgesi kararmasın)."""
    lp = nt.nodes.new("ShaderNodeLightPath")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    nt.links.new(shader, mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])


def _pus(nt, out, shader):
    """Kameradan uzaklaştıkça sıcak pusa karışır (havai perspektif)."""
    cam = nt.nodes.new("ShaderNodeCameraData")
    f = _aralik(nt, cam.outputs["View Distance"], PUS_BAS, PUS_SON, 0.0, PUS_MAKS)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = (*renk(PUS_RENK), 1.0)
    em.inputs[1].default_value = PUS_GUC
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(f, mx.inputs[0])
    nt.links.new(shader, mx.inputs[1])
    nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])


def _cikis(nt, out, shader, pus):
    if pus:
        _pus(nt, out, shader)
    else:
        nt.links.new(shader, out.inputs["Surface"])


def _resim(nt, yol, uzay, vec, proj="FLAT"):
    t = nt.nodes.new("ShaderNodeTexImage")
    im = bpy.data.images.load(yol, check_existing=True)
    try:
        im.colorspace_settings.name = uzay
    except Exception:
        pass
    t.image = im
    t.projection = proj
    if proj == "BOX":
        t.projection_blend = 0.3
    nt.links.new(vec, t.inputs["Vector"])
    return t


def _doku_renk(nt, anahtar, olcek, koord, proj, yedek, var=0.0, p=None, bump=0.25, rough=None):
    """Poly Haven dokusu (yoksa prosedürel yedek) renk çıkışı; p verilirse pürüz+kabartma bağlar."""
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / olcek, 1.0 / olcek, 1.0 / olcek)
    nt.links.new(_koord(nt, koord), mp.inputs["Vector"])
    vec = mp.outputs["Vector"]
    d = DOKU.get(anahtar)
    if d:
        c = _resim(nt, d["diff"], "sRGB", vec, proj).outputs["Color"]
        if p is not None:
            if rough is None:
                nt.links.new(_resim(nt, d["rough"], "Non-Color", vec, proj).outputs["Color"],
                             p.inputs["Roughness"])
            if bump > 0:
                _bump(nt, p, _resim(nt, d["disp"], "Non-Color", vec, proj).outputs["Color"], bump, 0.02)
    else:
        f = _gurultu(nt, vec, 3.0, 6.0)
        c = _rampa(nt, f, [(0.3, _kat(yedek, 0.85)), (0.7, _kat(yedek, 1.12))])
        if p is not None and bump > 0:
            _bump(nt, p, f, bump * 0.4, 0.02)
    if var > 0:
        g = _gurultu(nt, _koord(nt, "Position"), 0.012, 3.0)
        c = _olcekle(nt, c, _aralik(nt, g, 0.3, 0.7, 1.0 - var, 1.0 + var))
    return c


def mat_pbr(ad, anahtar, olcek, yedek_hex, ton=None, koord="Position", proj="FLAT", rough=None,
            bump=0.25, var=0.12, pus=True, spec=0.4):
    m, nt, out = _yeni_mat(ad)
    yed = renk(yedek_hex)
    p = _bsdf(nt, yed, rough if rough is not None else 0.8, spec=spec)
    c = _doku_renk(nt, anahtar, olcek, koord, proj, yed, var, p, bump, rough)
    if ton:
        c = _vmat(nt, 'MULTIPLY', c, ton)
    nt.links.new(c, p.inputs["Base Color"])
    _cikis(nt, out, p.outputs[0], pus)
    return m


def mat_duz(ad, hexr, rough=0.5, metal=0.0, spec=0.5, coat=0.0, var=0.06, olcek=1.5,
            bump=0.0, bump_olcek=None, koord="Object", pus=False):
    m, nt, out = _yeni_mat(ad)
    c = renk(hexr)
    p = _bsdf(nt, c, rough, metal, spec, coat)
    vec = _koord(nt, koord)
    if var > 0:
        fac = _gurultu(nt, vec, olcek)
        nt.links.new(_rampa(nt, fac, [(0.3, _kat(c, 1 - var)), (0.7, _kat(c, 1 + var))]),
                     p.inputs["Base Color"])
    if bump > 0:
        _bump(nt, p, _gurultu(nt, vec, bump_olcek or olcek * 10, 4.0), bump, 0.02)
    _cikis(nt, out, p.outputs[0], pus)
    return m


def mat_traverten(hexr):
    """Traverten: damar + gözenek + 60x120 cm panel derzleri."""
    m, nt, out = _yeni_mat("Traverten")
    c = renk(hexr)
    p = _bsdf(nt, c, 0.55, spec=0.4)
    vec = _koord(nt)
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Z'
    _ata(wv, 1.4, "Scale"); _ata(wv, 7.0, "Distortion"); _ata(wv, 3.0, "Detail")
    nt.links.new(vec, wv.inputs["Vector"])
    nz = _gurultu(nt, vec, 4.0, 8.0)
    fac = _matematik(nt, 'MULTIPLY_ADD', nz, 0.45, _matematik(nt, 'MULTIPLY', wv.outputs["Fac"], 0.55))
    tas = _rampa(nt, fac, [(0.25, _kat(c, 0.88)), (0.55, c), (0.85, _kat(c, 1.07))])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(vec, sep.inputs[0])
    yz = _matematik(nt, 'FRACT', _matematik(nt, 'DIVIDE', sep.outputs[2], 0.6))
    xy = _matematik(nt, 'FRACT', _matematik(nt, 'DIVIDE',
                                             _matematik(nt, 'ADD', sep.outputs[0], sep.outputs[1]), 1.2))
    derz = _matematik(nt, 'MAXIMUM', _matematik(nt, 'LESS_THAN', yz, 0.012),
                      _matematik(nt, 'LESS_THAN', xy, 0.006))
    nt.links.new(_karistir(nt, derz, tas, _kat(c, 0.62)), p.inputs["Base Color"])
    gozenek = _gurultu(nt, vec, 45.0, 3.0)
    _bump(nt, p, _matematik(nt, 'MULTIPLY_ADD', derz, -0.6, gozenek), 0.08, 0.01)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_ahsap(hexr):
    m, nt, out = _yeni_mat("Ahsap_Tik")
    c = renk(hexr)
    p = _bsdf(nt, c, 0.45, coat=0.25)
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    _ata(wv, 3.0, "Scale"); _ata(wv, 9.0, "Distortion"); _ata(wv, 4.0, "Detail")
    nt.links.new(_koord(nt), wv.inputs["Vector"])
    nt.links.new(_rampa(nt, wv.outputs["Fac"], [(0.2, _kat(c, 0.72)), (0.8, _kat(c, 1.18))]),
                 p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_cam_ic(hexr):
    """Cephe camı: üstte yansıtıcı cam katmanı, altında oda oda değişen iç mekân
    (tül perde / karanlık oda / yanan sıcak ışık)."""
    m, nt, out = _yeni_mat("Cephe_Cami")
    cam_rgb = renk(hexr)
    p = _bsdf(nt, cam_rgb, rough=0.6, spec=0.5, coat=1.0)
    _ata(p, 0.0, "Coat Roughness", "Clearcoat Roughness")
    _ata(p, 1.52, "Coat IOR")
    obj = _koord(nt)
    hucre = _vmat(nt, 'FLOOR', _vmat(nt, 'DIVIDE', _vmat(nt, 'SUBTRACT', obj, (0.0, 0.0, Z0)),
                                     (2.4, 2.4, KAT_H)))
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = '4D'
    nt.links.new(hucre, wn.inputs["Vector"])
    nt.links.new(oi.outputs["Random"], wn.inputs["W"])
    r = wn.outputs["Value"]
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    _ata(wv, 7.0, "Scale"); _ata(wv, 1.5, "Distortion")
    nt.links.new(_vmat(nt, 'ADD', obj, (0.0, 0.0, 0.0)), wv.inputs["Vector"])
    perde_c = renk(PALET["perde"])
    perde = _rampa(nt, wv.outputs["Fac"], [(0.0, _kat(perde_c, 0.72)), (1.0, perde_c)])
    ic = _karistir(nt, _matematik(nt, 'GREATER_THAN', r, 0.42), perde, renk("#3A322B"))
    ic = _vmat(nt, 'MULTIPLY', ic, (0.62, 0.70, 0.72))
    nt.links.new(ic, p.inputs["Base Color"])
    _ata(p, (*renk("#FFB774"), 1.0), "Emission Color", "Emission")
    nt.links.new(_matematik(nt, 'MULTIPLY', _matematik(nt, 'GREATER_THAN', r, 0.91), 1.4),
                 _ata(p, 0.0, "Emission Strength"))
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_seffaf(ad, hexr, ior=1.5, olcek=0.0, guc=0.0):
    m, nt, out = _yeni_mat(ad)
    p = _bsdf(nt, renk(hexr), rough=0.0, trans=1.0, ior=ior)
    if guc > 0:
        _bump(nt, p, _gurultu(nt, _koord(nt, "Position"), olcek, 3.0), guc, 0.05)
    _golge_seffaf(nt, out, p.outputs[0])
    return m


def mat_bitki(ad, hexr, olcek=2.5, pus=True, gecir=0.22):
    """Yaprak: ağaç başına ton farkı + arkadan ışık geçirgenliği."""
    m, nt, out = _yeni_mat(ad)
    c = renk(hexr)
    p = _bsdf(nt, c, 0.72, spec=0.32)
    vec = _koord(nt)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    fac = _gurultu(nt, vec, olcek, 5.0, w=oi.outputs["Random"])
    yap = _rampa(nt, fac, [(0.3, _kat(c, 0.6)), (0.55, c), (0.78, _kat(c, 1.35))])
    yap = _olcekle(nt, yap, _aralik(nt, oi.outputs["Random"], 0.0, 1.0, 0.82, 1.14))
    nt.links.new(yap, p.inputs["Base Color"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    _ata(vor, olcek * 4.0, "Scale")
    nt.links.new(vec, vor.inputs["Vector"])
    _bump(nt, p, vor.outputs["Distance"], 0.45, 0.1)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs[0].default_value = (*_kat(c, 1.5), 1.0)
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = gecir
    nt.links.new(p.outputs[0], mx.inputs[1])
    nt.links.new(tr.outputs[0], mx.inputs[2])
    _cikis(nt, out, mx.outputs[0], pus)
    return m


def mat_deniz():
    """Deniz: sığda turkuaz + yosun/kaya lekeleri, açıkta lacivert; dalga ve kıyı köpüğü."""
    m, nt, out = _yeni_mat("Deniz")
    p = _bsdf(nt, renk(PALET["deniz_derin"]), rough=0.035, spec=0.5, ior=1.333)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "kiyi"
    kiyi = at.outputs["Fac"]
    derin = renk(PALET["deniz_derin"])
    taban = _rampa(nt, kiyi, [(0.0, renk(PALET["deniz_kiyi"])), (0.18, renk(PALET["deniz_sig"])),
                              (0.55, _kat(derin, 1.15)), (1.0, _kat(derin, 0.8))])
    pos = _koord(nt, "Position")
    leke = _aralik(nt, _gurultu(nt, pos, 0.035, 5.0), 0.52, 0.62, 0.0, 1.0)
    bant = _matematik(nt, 'MULTIPLY', _aralik(nt, kiyi, 0.03, 0.10, 0.0, 1.0),
                      _aralik(nt, kiyi, 0.30, 0.55, 1.0, 0.0))
    taban = _karistir(nt, _matematik(nt, 'MULTIPLY', _matematik(nt, 'MULTIPLY', leke, bant), 0.8),
                      taban, renk(PALET["deniz_yosun"]))
    kopuk = _matematik(nt, 'MULTIPLY', _aralik(nt, kiyi, 0.0, 0.009, 0.75, 0.0),
                       _aralik(nt, _gurultu(nt, pos, 0.7, 4.0), 0.48, 0.62, 0.0, 1.0))
    nt.links.new(_karistir(nt, kopuk, taban, (0.86, 0.89, 0.88)), p.inputs["Base Color"])
    nt.links.new(_aralik(nt, kopuk, 0.0, 1.0, 0.035, 0.5), p.inputs["Roughness"])
    d1 = _gurultu(nt, pos, 0.045, 6.0)
    d2 = _gurultu(nt, pos, 0.5, 4.0)
    d3 = _gurultu(nt, pos, 2.6, 2.0)
    h = _matematik(nt, 'MULTIPLY_ADD', d2, 0.45, d1)
    _bump(nt, p, _matematik(nt, 'MULTIPLY_ADD', d3, 0.12, h), 0.55, 0.6)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_komsu_duvar(renkler):
    """Komşu evler: sıva dokusu × ev başına ton + prosedürel pencere düzeni."""
    m, nt, out = _yeni_mat("Komsu_Duvar")
    p = _bsdf(nt, renkler[0], 0.8, spec=0.3)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "ton"
    n = len(renkler) - 1
    ton = _rampa(nt, at.outputs["Fac"], [(i / n, c) for i, c in enumerate(renkler)])
    siva = _doku_renk(nt, "siva", 2.5, "Position", "BOX", (0.8, 0.8, 0.8), 0.0, p, 0.12, rough=0.85)
    duvar = _vmat(nt, 'MULTIPLY', siva, ton) if DOKU.get("siva") else ton
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(_koord(nt, "Position"), sep.inputs[0])
    yatay = _matematik(nt, 'FRACT', _matematik(nt, 'DIVIDE',
                                               _matematik(nt, 'ADD', sep.outputs[0], sep.outputs[1]), 3.2))
    dusey = _matematik(nt, 'FRACT', _matematik(nt, 'DIVIDE', sep.outputs[2], 3.0))
    mx = _matematik(nt, 'MULTIPLY', _matematik(nt, 'GREATER_THAN', yatay, 0.30),
                    _matematik(nt, 'LESS_THAN', yatay, 0.70))
    mz = _matematik(nt, 'MULTIPLY', _matematik(nt, 'GREATER_THAN', dusey, 0.36),
                    _matematik(nt, 'LESS_THAN', dusey, 0.82))
    maske = _matematik(nt, 'MULTIPLY', mx, mz)
    nt.links.new(_karistir(nt, maske, duvar, renk("#2A3238")), p.inputs["Base Color"])
    nt.links.new(_matematik(nt, 'MULTIPLY_ADD', maske, -0.65, 0.85), p.inputs["Roughness"])
    _cikis(nt, out, p.outputs[0], True)
    return m


def mat_kiremit():
    m, nt, out = _yeni_mat("Komsu_Kiremit")
    yed = renk(PALET["ev_cati"])
    p = _bsdf(nt, yed, 0.7, spec=0.35)
    c = _doku_renk(nt, "kiremit", 2.5, "Position", "BOX", yed, 0.0, p, 0.3)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "ton"
    ton = _rampa(nt, at.outputs["Fac"], [(0.0, (0.78, 0.72, 0.70)), (0.5, (1.0, 1.0, 1.0)),
                                         (1.0, (1.10, 0.95, 0.85))])
    nt.links.new(_vmat(nt, 'MULTIPLY', c, ton), p.inputs["Base Color"])
    _cikis(nt, out, p.outputs[0], True)
    return m


def mat_tonlu(ad, renkler, rough=0.7, pus=True):
    """Ev başına farklı renk ('ton' attribute): tente vb."""
    m, nt, out = _yeni_mat(ad)
    p = _bsdf(nt, renkler[0], rough, spec=0.35)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "ton"
    n = len(renkler) - 1
    nt.links.new(_rampa(nt, at.outputs["Fac"], [(i / n, c) for i, c in enumerate(renkler)]),
                 p.inputs["Base Color"])
    _cikis(nt, out, p.outputs[0], pus)
    return m


def mat_gunes_paneli():
    m, nt, out = _yeni_mat("Gunes_Paneli")
    p = _bsdf(nt, renk(PALET["gunes_panel"]), 0.12, spec=0.6, coat=0.6)
    br = nt.nodes.new("ShaderNodeTexBrick")
    _ata(br, 1.0, "Scale"); _ata(br, 0.02, "Mortar Size"); _ata(br, 0.25, "Brick Width")
    _ata(br, 2.0, "Row Height")
    br.inputs["Color1"].default_value = (*renk(PALET["gunes_panel"]), 1)
    br.inputs["Color2"].default_value = (*_kat(renk(PALET["gunes_panel"]), 1.2), 1)
    br.inputs["Mortar"].default_value = (0.55, 0.57, 0.6, 1)
    nt.links.new(_koord(nt), br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    _cikis(nt, out, p.outputs[0], True)
    return m


def mat_arazi():
    """Arazi: kuru Akdeniz çayırı (doku), bahçe yeşili lekeleri, yamaçta orman tabanı,
    kıyıda çakıllı kum + ıslak şerit, uzakta sıcak pus."""
    m, nt, out = _yeni_mat("Arazi")
    p = _bsdf(nt, renk(PALET["arazi"]), 0.92, spec=0.3)
    pos = _koord(nt, "Position")
    zemin = _doku_renk(nt, "arazi", 18.0, "Position", "FLAT", renk(PALET["arazi"]), 0.18)
    zemin = _vmat(nt, 'MULTIPLY', zemin, (0.86, 1.0, 0.74))
    yesil = _aralik(nt, _gurultu(nt, pos, 0.022, 5.0), 0.46, 0.60, 0.0, 0.7)
    zemin = _karistir(nt, yesil, zemin, _vmat(nt, 'MULTIPLY', zemin, (0.55, 0.95, 0.42)))
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(pos, sep.inputs[0])
    orm = nt.nodes.new("ShaderNodeAttribute")
    orm.attribute_name = "orman"
    tepe = _matematik(nt, 'MAXIMUM', _aralik(nt, sep.outputs[2], 3.0, 26.0, 0.0, 1.0),
                      _aralik(nt, orm.outputs["Fac"], 0.0, 0.5, 0.0, 1.0))
    orman_c = renk(PALET["orman"])
    orman = _rampa(nt, _gurultu(nt, pos, 0.006, 8.0), [(0.38, _kat(orman_c, 0.62)), (0.52, orman_c),
                                                       (0.66, _kat(orman_c, 1.25)),
                                                       (0.74, renk("#6E7448"))])
    c = _karistir(nt, tepe, zemin, orman)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "kumsal"
    kum = _doku_renk(nt, "kumsal", 26.0, "Position", "FLAT", renk(PALET["kum"]), 0.10)
    kum = _karistir(nt, _aralik(nt, sep.outputs[2], -0.45, -0.12, 0.55, 0.0), kum,
                    _vmat(nt, 'MULTIPLY', kum, (0.62, 0.60, 0.56)))
    c = _karistir(nt, at.outputs["Fac"], c, kum)
    nt.links.new(c, p.inputs["Base Color"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    _ata(vor, 0.18, "Scale")
    nt.links.new(pos, vor.inputs["Vector"])
    ince = _gurultu(nt, pos, 3.0, 4.0)
    h = _matematik(nt, 'MULTIPLY', vor.outputs["Distance"], tepe)
    _bump(nt, p, _matematik(nt, 'MULTIPLY_ADD', ince, 0.08, h), 0.4, 1.0)
    _cikis(nt, out, p.outputs[0], True)
    return m


def mat_karo(ad, hexr, boy=0.6, rough=0.6):
    m, nt, out = _yeni_mat(ad)
    c = renk(hexr)
    p = _bsdf(nt, c, rough, spec=0.4)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.5
    _ata(br, 1.0, "Scale"); _ata(br, 0.006, "Mortar Size"); _ata(br, boy * 2, "Brick Width")
    _ata(br, boy, "Row Height"); _ata(br, 0.15, "Bias")
    br.inputs["Color1"].default_value = (*_kat(c, 0.95), 1)
    br.inputs["Color2"].default_value = (*_kat(c, 1.05), 1)
    br.inputs["Mortar"].default_value = (*_kat(c, 0.7), 1)
    nt.links.new(_koord(nt), br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def malzemeler():
    P = PALET
    tas = (mat_pbr("Tas_Kaplama", "tas", 2.0, P["tas"], ton=(1.12, 1.10, 1.06), koord="Object",
                   proj="FLAT", var=0.06, pus=False) if DOKU.get("tas")
           else mat_karo("Tas_Kaplama", P["tas"], 0.6))
    M = {
        "beyaz": mat_duz("Beyaz_Kompozit", P["beyaz"], 0.42, var=0.03),
        "traverten": mat_traverten(P["traverten"]),
        "antrasit": mat_duz("Antrasit", P["antrasit"], 0.38, coat=0.15, var=0.05),
        "kaide": mat_duz("Bazalt_Kaide", P["kaide"], 0.6, var=0.12, olcek=3, bump=0.1),
        "bronz": mat_duz("Sampanya_Bronz", P["bronz"], 0.30, metal=1.0, var=0.04),
        "ahsap": mat_ahsap(P["ahsap"]),
        "cam": mat_cam_ic(P["cam"]),
        "korkuluk": mat_seffaf("Cam_Korkuluk", P["korkuluk"]),
        "tas": tas,
        "minder": mat_duz("Minder", P["minder"], 0.9, spec=0.2, var=0.03),
        "yesil": mat_bitki("Bitki_Cit", P["yesil"], pus=False),
        "cati_yesil": mat_bitki("Yesil_Cati", P["cati_yesil"], 4.0, pus=False, gecir=0.1),
        "cim": mat_pbr("Cim", "cim", 2.6, P["cim"], ton=(0.88, 1.05, 0.80), koord="Position",
                       var=0.22, pus=False, rough=0.9, bump=0.15),
        "havuz": mat_karo("Havuz_Seramik", P["havuz"], 0.25, rough=0.25),
        "su": mat_seffaf("Havuz_Suyu", "#DDF6F4", 1.333, 1.8, 0.10),
        "asfalt": mat_pbr("Asfalt", "asfalt", 30.0, P["asfalt"], ton=(0.82, 0.82, 0.83), var=0.10,
                          bump=0.15),
        "kaldirim": (mat_pbr("Kaldirim", "tas", 1.6, P["kaldirim"], ton=(0.85, 0.85, 0.85),
                             koord="Position", proj="BOX", var=0.05) if DOKU.get("tas")
                     else mat_karo("Kaldirim", P["kaldirim"], 0.4, 0.75)),
        "cizgi": mat_duz("Yol_Cizgisi", P["cizgi"], 0.6, var=0.08, olcek=3, pus=True),
        "deniz": mat_deniz(),
        "arazi": mat_arazi(),
        "ev_duvar": mat_komsu_duvar([renk("#E9D9B8"), renk("#F1ECE4"), renk("#E2C59A"),
                                     renk("#E6CDBE"), renk("#D8D3C7"), renk("#EADBC0")]),
        "ev_cati": mat_kiremit(),
        "duz_cati": mat_duz("Duz_Cati", "#B9B4AA", 0.8, var=0.1, pus=True),
        "bahce_duvar": mat_pbr("Bahce_Duvari", "siva", 2.5, P["ev_duvar"], ton=(0.95, 0.92, 0.86),
                               proj="BOX", var=0.10, bump=0.1),
        "gunes_panel": mat_gunes_paneli(),
        "tank": mat_duz("Tank_Beyaz", P["tank"], 0.35, var=0.03, pus=True),
        "tank_siyah": mat_duz("Tank_Siyah", "#1A1B1C", 0.4, var=0.03, pus=True),
        "demir": mat_duz("Demir_Korkuluk", P["demir"], 0.45, metal=0.6, var=0.0, pus=True),
        "metal": mat_duz("Metal_Gri", P["metal"], 0.4, metal=0.8, var=0.05, pus=True),
        "tente": mat_tonlu("Tente", [renk("#2F5E8C"), renk("#C8553D"), renk("#E4D9C2"),
                                     renk("#3D7A57"), renk("#D9A441")], 0.85),
        "iskele": mat_duz("Iskele", "#C9C2B4", 0.8, var=0.1, olcek=2),
        "tekne": mat_duz("Tekne", "#F4F4F2", 0.25, coat=0.6, var=0.0),
        "araba_cam": mat_duz("Araba_Cami", "#16191C", 0.08, spec=0.6, coat=1.0, var=0.0, pus=True),
        "lastik": mat_duz("Lastik", "#121212", 0.7, var=0.0, pus=True),
        "ten": mat_duz("Ten", P["ten"], 0.6, var=0.12, olcek=6),
        "kumas": mat_tonlu("Kumas", [renk("#B03A2E"), renk("#2D5D9F"), renk("#F2F0EA"),
                                     renk("#1F1F22"), renk("#E2B13C"), renk("#3C8D6E")], 0.9,
                           pus=False),
        "semsiye": mat_tonlu("Semsiye", [renk("#F3F1EA"), renk("#1F6FA8"), renk("#E06A2C"),
                                         renk("#F3F1EA"), renk("#E9C341")], 0.8, pus=False),
        "yaprak": mat_bitki("Agac_Yaprak", P["yaprak"], 1.6),
        "zeytin": mat_bitki("Zeytin_Yaprak", P["zeytin"], 1.8),
        "cam_yaprak": mat_bitki("Cam_Yaprak", P["cam_yaprak"], 2.4),
        "palmiye": mat_bitki("Palmiye_Yaprak", P["palmiye"], 2.0),
        "govde": mat_duz("Agac_Govde", P["govde"], 0.85, var=0.15, olcek=4, pus=True),
    }
    for ad, hx in (("beyaz", "#EDEDEA"), ("gumus", "#A9ADB1"), ("siyah", "#141518"),
                   ("koyu", "#3C4146"), ("kirmizi", "#8E1C1C"), ("mavi", "#1E3E6E"), ("bej", "#B7A58A")):
        M["araba_" + ad] = mat_duz("Araba_" + ad, hx, 0.22, metal=0.5, coat=1.0, var=0.0, pus=True)
    return M


# ============================== BLOK TİPİ ==============================
def teras_konturu(o=0.0):
    W2, D2 = B_W / 2, B_D / 2
    bw, yn = W2 + 0.05 + o, D2 + 0.05 + o
    xr, ys, yr, r = W2 + DONUS_W + o, -D2 - TERAS_D - o, -D2 + DONUS_L + o, R_KOSE + o
    return ([(bw, yn), (-bw, yn), (-bw, yr), (-xr, yr)] +
            _yay(-xr + r, ys + r, r, 180, 270) + _yay(xr - r, ys + r, r, 270, 360) +
            [(xr, yr), (bw, yr)])


def korkuluk_hatti(sx):
    W2, D2, i = B_W / 2, B_D / 2, 0.07
    xr, ys, yr, r = W2 + DONUS_W - i, -D2 - TERAS_D + i, -D2 + DONUS_L - i, R_KOSE - i
    pts = [(W2 + 0.02, yr), (xr, yr)] + _yay(xr - r, ys + r, r, 0, -90) + [(0.22, ys)]
    return pts if sx > 0 else [(-x, y) for x, y in reversed(pts)]


def u_hatti(o):
    W2, D2 = B_W / 2, B_D / 2
    xr, ys, yr, r = W2 + DONUS_W + o, -D2 - TERAS_D - o, -D2 + DONUS_L + o, R_KOSE + o
    return ([(-xr, yr)] + _yay(-xr + r, ys + r, r, 180, 270) +
            _yay(xr - r, ys + r, r, 270, 360) + [(xr, yr)])


def _kasa(g, nx, ny, w0, a0, a1, z0, z1, mat, t=0.06, d=0.10):
    """Duvar düzleminde dikdörtgen pencere kasası; (nx,ny) dış normal."""
    def parca(lo, hi, zl, zh):
        if nx:
            xa, xb = sorted((w0, w0 + nx * d))
            g.kutu(xa, xb, lo, hi, zl, zh, mat)
        else:
            ya, yb = sorted((w0, w0 + ny * d))
            g.kutu(lo, hi, ya, yb, zl, zh, mat)
    parca(a0 - t, a1 + t, z0 - t, z0)
    parca(a0 - t, a1 + t, z1, z1 + t)
    parca(a0 - t, a0, z0, z1)
    parca(a1, a1 + t, z0, z1)


def _teras_mobilya(g, M, z, sx, kat):
    """Teras: tek katlarda iki şezlong, çift katlarda yemek masası + saksıda zeytin."""
    D2, W2 = B_D / 2, B_W / 2
    ym = -D2 - 0.85
    if kat % 2:
        for xc in (1.35, 3.40):
            x = sx * xc
            g.kutu(x - 0.92, x + 0.92, ym - 0.32, ym + 0.32, z + 0.12, z + 0.30, M["ahsap"])
            g.kutu(x - 0.90, x + 0.52, ym - 0.30, ym + 0.30, z + 0.30, z + 0.38, M["minder"])
            g.kutu_m((x + sx * 0.70, ym, z + 0.52), (0.24, 0.30, 0.05),
                     Matrix.Rotation(math.radians(-55 * sx), 3, 'Y'), M["minder"])
    else:
        x = sx * 2.3
        g.kutu(x - 0.55, x + 0.55, ym - 0.38, ym + 0.38, z + 0.72, z + 0.76, M["ahsap"])
        g.kutu(x - 0.05, x + 0.05, ym - 0.05, ym + 0.05, z, z + 0.72, M["bronz"])
        for dx in (-0.95, 0.95):
            g.kutu(x + dx - 0.22, x + dx + 0.22, ym - 0.22, ym + 0.22, z + 0.42, z + 0.47, M["minder"])
            g.kutu(x + dx - 0.22, x + dx + 0.22, ym + 0.17, ym + 0.22, z + 0.47, z + 0.85, M["ahsap"])
        px, py = sx * (W2 + 0.35), -D2 - 1.05
        g.silindir((px, py, z), (px, py, z + 0.55), 0.28, M["antrasit"], 10)
        g.silindir((px, py, z + 0.55), (px, py, z + 1.25), 0.04, M["ahsap"], 6)
        g.kure((px, py, z + 1.55), (0.52, 0.50, 0.42), M["zeytin"], 10, 6, 0.25, kat * 1.7 + sx)


def blok_tipi(M, coll):
    g = Govde()
    W2, D2 = B_W / 2, B_D / 2
    ys, yr, xr = -D2 - TERAS_D, -D2 + DONUS_L, W2 + DONUS_W
    Zc = Z0 + KAT * KAT_H                    # çatı döşemesi üstü
    Zt = Zc - DOSEME_T                       # gövde üstü
    cy = D2 + CEK_C                          # çekirdek kuzey yüzü

    # zemin: çevre taşı, bahçe çiti, bazalt kaide + zemin kat terası
    g.kutu(-W2 - 1.8, W2 + 1.8, -D2, D2 + 2.6, 0.0, 0.05, M["tas"], alt=False)
    g.serit(u_hatti(0.95), 0.0, 1.0, 0.55, M["yesil"])
    g.prizma(teras_konturu(0.30), 0.0, Z0, M["kaide"], ust=M["tas"], alt=False)

    # gövde + iki daireyi ayıran, denize uzanan traverten bıçak duvar
    g.kutu(-W2, W2, -D2, D2, Z0, Zt, M["traverten"], ust=False, alt=False)
    g.kutu(-0.20, 0.20, ys - 0.15, -D2, Z0, Zt, M["traverten"], ust=False, alt=False)

    # ara döşemeler: beyaz alın, tik tavan, çerçevesiz cam korkuluk, saksı, teras mobilyası
    for i in range(1, KAT):
        z = Z0 + i * KAT_H
        g.prizma(teras_konturu(0.0), z - DOSEME_T, z, M["beyaz"], ust=M["tas"], alt=M["ahsap"])
        for sx in (-1, 1):
            h = korkuluk_hatti(sx)
            g.serit(h, z, z + 1.05, 0.024, M["korkuluk"])
            g.serit(h, z + 1.05, z + 1.085, 0.05, M["bronz"])
            xa, xb = sorted((sx * (W2 + 0.12), sx * (xr - 0.14)))
            g.kutu(xa, xb, yr - 0.70, yr - 0.16, z, z + 0.45, M["antrasit"])
            g.kutu(xa + 0.05, xb - 0.05, yr - 0.66, yr - 0.20, z + 0.45, z + 1.0, M["yesil"])
            _teras_mobilya(g, M, z, sx, i)

    # çatı: yüzer saçak, yeşil çatı, çekirdek kulesi
    g.prizma(teras_konturu(0.35), Zt, Zc + 0.20, M["beyaz"], ust=M["beyaz"], alt=M["ahsap"])
    g.kutu(-W2 + 0.5, W2 - 0.5, -D2 + 0.3, D2 - 0.5, Zc + 0.20, Zc + 0.30, M["cati_yesil"],
           alt=False)
    g.kutu(-CEK_W / 2, CEK_W / 2, D2 - 0.5, cy, 0.0, Zc + 2.3, M["antrasit"])
    g.kutu(-1.3, 1.3, 2.2, D2 - 0.5, Zc + 0.20, Zc + 2.3, M["traverten"], alt=False)

    # giriş: cam kapı, merdiven ışık şeridi, tik altlı saçak
    g.kutu(-0.95, 0.95, cy - 0.02, cy + 0.02, 0.05, 2.70, M["cam"])
    _kasa(g, 0, 1, cy, -0.95, 0.95, 0.05, 2.70, M["bronz"])
    g.kutu(-0.35, 0.35, cy - 0.02, cy + 0.02, 3.6, Zc + 1.9, M["cam"])
    g.kutu(-2.2, 2.2, cy, cy + 1.6, 3.05, 3.30, M["beyaz"], alt=M["ahsap"])

    # yan cephelerde sürekli bronz fin perdesi (yatak odası bandının önünde)
    for sx in (-1, 1):
        xa, xb = sorted((sx * (W2 + 0.03), sx * (W2 + 0.42)))
        for k in range(6):
            y = -0.35 + k * 0.46
            g.kutu(xa, xb, y - 0.03, y + 0.03, Z0, Zt, M["bronz"])

    for i in range(KAT):
        zf = Z0 + i * KAT_H
        zt = Z0 + (i + 1) * KAT_H - DOSEME_T
        for sx in (-1, 1):
            # deniz cephesi: yerden tavana sürme cam, bronz kayıt/dikme
            xa, xb = sorted((sx * 0.20, sx * (W2 - 0.04)))
            g.kutu(xa, xb, -D2 - 0.02, -D2 + 0.02, zf, zt, M["cam"])
            g.kutu(xa, xb, -D2 - 0.07, -D2, zf, zf + 0.06, M["bronz"])
            g.kutu(xa, xb, -D2 - 0.07, -D2, zt - 0.07, zt, M["bronz"])
            for k in range(4):
                x = xa + (xb - xa) * k / 3
                g.kutu(x - 0.03, x + 0.03, -D2 - 0.09, -D2, zf, zt, M["bronz"])
            # salon köşesi: çerçevesiz köşe cam (yan cephe)
            x0 = sx * W2
            xa, xb = sorted((x0 - sx * 0.02, x0 + sx * 0.02))
            g.kutu(xa, xb, -D2 - 0.02, yr - 0.06, zf, zt, M["cam"])
            xa, xb = sorted((x0, x0 + sx * 0.08))
            ym = (-D2 + yr) / 2
            g.kutu(xa, xb, ym - 0.03, ym + 0.03, zf, zt, M["bronz"])
            g.kutu(xa, xb, yr - 0.12, yr - 0.06, zf, zt, M["bronz"])
            # yatak odası bandı (fin arkası) + ikinci pencere
            xa, xb = sorted((x0 - sx * 0.01, x0 + sx * 0.03))
            g.kutu(xa, xb, -0.40, 2.00, zf + 0.10, zt - 0.05, M["cam"])
            g.kutu(xa, xb, 3.30, 4.40, zf + 0.95, zt - 0.15, M["cam"])
            _kasa(g, sx, 0, x0, 3.30, 4.40, zf + 0.95, zt - 0.15, M["bronz"])
            # kuzey cephesi pencereleri
            xa, xb = sorted((sx * 2.10, sx * 4.20))
            g.kutu(xa, xb, D2 - 0.01, D2 + 0.03, zf + 0.90, zt - 0.12, M["cam"])
            _kasa(g, 0, 1, D2, xa, xb, zf + 0.90, zt - 0.12, M["bronz"])
    return g.obje("BLOK_TIPI", coll)


# ============================== AĞAÇ TİPLERİ ==============================
def _govde_prizma(g, r, z0, z1, mat, kenar=7, ox=0.0, oy=0.0):
    g.prizma([(ox + r * math.cos(2 * math.pi * a / kenar), oy + r * math.sin(2 * math.pi * a / kenar))
              for a in range(kenar)], z0, z1, mat)


def agac_tipleri(M, ust):
    tipler = {}

    def yeni(ad):
        c = bpy.data.collections.new(ad)
        ust.children.link(c)
        tipler[ad] = c
        return c

    # yaprak döken / çınar-dut tipi: kümeli taç
    g = Govde()
    _govde_prizma(g, 0.22, 0, 3.0, M["govde"])
    for (dx, dy, dz, r) in ((0, 0, 4.3, 2.3), (1.1, 0.5, 4.9, 1.6), (-0.9, 0.8, 5.1, 1.5),
                            (0.3, -1.0, 5.4, 1.4), (-0.6, -0.5, 3.6, 1.6)):
        g.kure((dx, dy, dz), (r, r * 0.95, r * 0.82), M["yaprak"], 12, 8, 0.32, dx * 3 + dy)
    g.obje("agac_yuvarlak", yeni("AGAC_YUVARLAK"))

    # zeytin: kısa eğri gövde, gümüşi kümeler
    g = Govde()
    _govde_prizma(g, 0.2, 0, 1.2, M["govde"], 6)
    _govde_prizma(g, 0.14, 1.1, 1.9, M["govde"], 6, 0.25, 0.1)
    for (dx, dy, dz, r) in ((0.2, 0.1, 2.6, 1.7), (1.0, -0.4, 2.9, 1.1), (-0.8, 0.6, 2.8, 1.2)):
        g.kure((dx, dy, dz), (r, r * 0.95, r * 0.7), M["zeytin"], 12, 8, 0.35, dx * 5 + dy)
    g.obje("zeytin", yeni("AGAC_ZEYTIN"))

    # servi
    g = Govde()
    _govde_prizma(g, 0.15, 0, 1.0, M["govde"], 6)
    g.kure((0, 0, 4.4), (0.85, 0.85, 4.0), M["yaprak"], 10, 9, 0.12, 3.0)
    g.obje("servi", yeni("AGAC_SERVI"))

    # fıstık çamı: uzun eğik gövde, yassı şemsiye taç
    g = Govde()
    for k in range(6):
        z0, z1 = 7.6 * k / 6, 7.6 * (k + 1) / 6
        _govde_prizma(g, 0.30 - 0.025 * k, z0, z1, M["govde"], 7, 0.55 * (k / 6) ** 1.5, 0.0)
    for (dx, dy, dz, r) in ((0.6, 0, 8.4, 3.0), (2.1, 0.9, 8.1, 1.9), (-1.0, -1.1, 8.2, 2.0),
                            (0.4, 1.6, 8.6, 1.8)):
        g.kure((dx, dy, dz), (r, r * 0.95, r * 0.42), M["cam_yaprak"], 14, 7, 0.3, dx + dy * 2)
    g.obje("fistik_cami", yeni("AGAC_CAM"))

    # kızılçam (tepelerdeki orman): düzensiz konik, iki varyant
    for v, (h, s) in enumerate(((7.5, 1.0), (10.0, 1.25))):
        g = Govde()
        _govde_prizma(g, 0.2 * s, 0, h * 0.55, M["govde"], 6)
        for (dz, r, ox) in ((0.42, 1.9, 0.2), (0.62, 1.5, -0.3), (0.80, 1.1, 0.25), (0.95, 0.6, 0.0)):
            g.kure((ox * s, 0.15 * s, h * dz), (r * s, r * s * 0.9, r * s * 0.75), M["cam_yaprak"],
                   10, 7, 0.35, v * 3 + dz * 5)
        g.obje(f"kizilcam_{v}", yeni(f"AGAC_KIZILCAM_{v}"))

    # palmiye: halka dokulu gövde, iki kat yaprak
    g = Govde()
    H = 7.2
    for k in range(7):
        z0, z1 = H * k / 7, H * (k + 1) / 7
        r = 0.26 - 0.012 * k
        ox = 0.35 * (k / 7) ** 2
        g.prizma([(ox + r * math.cos(a * math.pi / 4), r * math.sin(a * math.pi / 4))
                  for a in range(8)], z0, z1, M["govde"], ust=False, alt=False)
    top = (0.35, 0.0, H)
    for k in range(15):
        ust_kat = k % 2
        a = 2 * math.pi * k / 15 + 0.3 * math.sin(k * 2.1)
        ca, sa = math.cos(a), math.sin(a)
        b = len(g.v)
        sira = []
        boy = 3.6 if ust_kat else 3.2
        for s in range(7):
            t = s / 6
            L = boy * t
            z = H + (1.1 if ust_kat else 0.7) * t - (2.0 if ust_kat else 2.8) * t * t
            w = 0.6 * (1 - t) + 0.07
            cx, cy = top[0] + ca * L, top[1] + sa * L
            sira += [(cx - sa * w, cy + ca * w, z), (cx + sa * w, cy - ca * w, z - 0.15 * t)]
        g._v(sira)
        for s in range(6):
            q = b + 2 * s
            g.yuz((q, q + 1, q + 3, q + 2), M["palmiye"])
    g.kure(top, (0.45, 0.45, 0.35), M["palmiye"], 8, 5)
    g.obje("palmiye", yeni("AGAC_PALMIYE"))

    orman = bpy.data.collections.new("YALOVA_ORMAN_TIPLERI")
    ust.children.link(orman)
    for ad in ("AGAC_KIZILCAM_0", "AGAC_KIZILCAM_1", "AGAC_CAM", "AGAC_YUVARLAK"):
        orman.children.link(tipler[ad])
    tipler["ORMAN"] = orman
    return tipler


# ============================== ARAÇLAR ==============================
def araba_tipleri(M, ust):
    """Sedan ve SUV gövdesi x renk; araç boyu +X yönünde."""
    tipler = []
    for i, renk_ad in enumerate(("beyaz", "gumus", "siyah", "beyaz", "koyu", "kirmizi", "mavi",
                                 "gumus", "bej", "beyaz")):
        suv = i % 3 == 2
        g = Govde()
        boya = M["araba_" + renk_ad]
        if suv:
            L, W, cam_ust = 4.6, 1.86, 1.72
            g.profil([(-2.3, 0.32), (2.3, 0.32), (2.35, 0.75), (2.15, 1.0), (-2.3, 1.02),
                      (-2.35, 0.72)], -W / 2, W / 2, boya)
            g.profil([(1.25, 0.98), (0.75, cam_ust), (-2.2, cam_ust), (-2.25, 0.98)], -W / 2 + 0.07,
                     W / 2 - 0.07, M["araba_cam"])
            g.kutu(-2.18, 0.72, -W / 2 + 0.1, W / 2 - 0.1, cam_ust - 0.02, cam_ust + 0.05, boya)
        else:
            L, W = 4.45, 1.78
            g.profil([(-2.2, 0.30), (2.2, 0.30), (2.25, 0.62), (2.0, 0.82), (-2.05, 0.88),
                      (-2.25, 0.66)], -W / 2, W / 2, boya)
            g.profil([(1.05, 0.84), (0.35, 1.38), (-1.0, 1.40), (-1.75, 0.88)], -W / 2 + 0.1,
                     W / 2 - 0.1, M["araba_cam"])
            g.kutu(-0.95, 0.3, -W / 2 + 0.16, W / 2 - 0.16, 1.36, 1.42, boya)
        for x in (-L / 2 + 0.85, L / 2 - 0.85):
            for y in (-W / 2 + 0.05, W / 2 - 0.27):
                g.silindir((x, y, 0.33), (x, y + 0.22, 0.33), 0.33, M["lastik"], 10)
        c = bpy.data.collections.new(f"ARABA_{i}")
        ust.children.link(c)
        g.obje(f"araba_{i}", c)
        tipler.append(c)
    return tipler


# ============================== KIYI / ARAZİ ==============================
def _kiyi_hazirla():
    pts = list(KIYI)
    (x0, y0), (x1, y1) = pts[0], pts[1]
    l = math.hypot(x0 - x1, y0 - y1)
    pts.insert(0, (x0 + (x0 - x1) / l * 3400, y0 + (y0 - y1) / l * 3400))
    (x0, y0), (x1, y1) = pts[-1], pts[-2]
    l = math.hypot(x0 - x1, y0 - y1)
    pts.append((x0 + (x0 - x1) / l * 3200, y0 + (y0 - y1) / l * 3200))
    for _ in range(3):                       # Chaikin yumuşatma
        yeni = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            yeni += [(0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by),
                     (0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by)]
        yeni.append(pts[-1])
        pts = yeni
    U = np.array([p[0] for p in pts])
    V = np.array([p[1] for p in pts])
    ug = np.arange(U[0], U[-1], 1.0)
    vg = np.interp(ug, U, V)
    return ug, vg, np.gradient(vg, ug)


KU, KV, KS = _kiyi_hazirla()
_KD = kdtree.KDTree(len(KU))
for _i, (_x, _y) in enumerate(zip(KU.tolist(), KV.tolist())):
    _KD.insert((_x, _y, 0.0), _i)
_KD.balance()


def kiyi_v(u):
    return np.interp(u, KU, KV)


def kiyi_d(u, v):
    """Kıyı çizgisine en kısa mesafe (m); kara tarafı +, deniz tarafı -."""
    u, v = np.asarray(u, dtype=float), np.asarray(v, dtype=float)
    shp, uu, vv = u.shape, u.reshape(-1), v.reshape(-1)
    bul = _KD.find
    d = np.fromiter((bul((x, y, 0.0))[2] for x, y in zip(uu.tolist(), vv.tolist())), float, len(uu))
    isaret = np.where(vv >= np.interp(uu, KU, KV), 1.0, -1.0)
    return (d * isaret).reshape(shp)


def kiyi_nokta(u, d):
    """Kıyıdan dik d metre uzaklıktaki nokta (yaklaşık): (u, v)."""
    s = float(np.interp(u, KU, KS))
    return u, float(kiyi_v(u)) + d * math.sqrt(1.0 + s * s)


def kumsal_z(d):
    return float(-0.75 + 0.75 * smooth(-8.0, 12.0, d))


def _kolonlar():
    ince = np.arange(-460.0, 660.0, 5.0)
    orta_b = np.arange(-1500.0, -460.0, 40.0)
    orta_d = np.arange(700.0, 1740.0, 40.0)
    kaba_b = np.array([-3000, -2500, -2000, -1750])
    kaba_d = np.array([2000, 2400, 2800, 3100])
    return np.concatenate([kaba_b, orta_b, ince, orta_d, kaba_d]).astype(float)


def _grid_mesh(ad, us, ofs, z_fn, attrs, mat, coll):
    nu, no = len(us), len(ofs)
    U = np.repeat(us[:, None], no, 1)
    V = kiyi_v(U) + ofs[None, :]
    D = kiyi_d(U, V)
    Z = z_fn(U, V, D)
    verts = np.stack([U, V, Z], -1).reshape(-1, 3)
    faces = []
    for i in range(nu - 1):
        for j in range(no - 1):
            a = i * no + j
            faces.append((a, a + no, a + no + 1, a + 1))
    me = bpy.data.meshes.new(ad)
    me.from_pydata(verts.tolist(), [], faces)
    me.materials.append(mat)
    for an, fn in attrs.items():
        at = me.attributes.new(an, 'FLOAT', 'POINT')
        at.data.foreach_set("value", fn(U, V, D).reshape(-1).tolist())
    me.update()
    ob = bpy.data.objects.new(ad, me)
    coll.objects.link(ob)
    return ob


def arazi_z(U, V, D):
    Z = np.where(D < 12.0, -0.75 + 0.75 * smooth(-8.0, 12.0, D), 0.0)
    t = smooth(380.0, 1000.0, D)
    tepe = np.zeros_like(U)
    idx = np.nonzero(t > 0)
    for i, j in zip(*idx):
        u, v = U[i, j], V[i, j]
        n1 = noise.noise(Vector((u / 700.0, v / 700.0, 0.3)))
        n2 = noise.noise(Vector((u / 210.0, v / 210.0, 2.1)))
        tepe[i, j] = 240.0 + 150.0 * n1 + 45.0 * n2
    return Z + t * tepe


def orman_maske(U, V, D):
    yamac = smooth(385.0, 470.0, D) * smooth(-1450.0, -1150.0, U) * (1.0 - smooth(1350.0, 1650.0, U))
    acik = np.array([[noise.noise(Vector((u / 160.0, v / 160.0, 5.5))) for u, v in zip(ru, rv)]
                     for ru, rv in zip(U, V)])
    return yamac * np.clip(0.9 + 0.9 * acik, 0.0, 1.0) * (D < 2700)


def deniz_ve_arazi(M, coll):
    us = _kolonlar()
    kara = np.concatenate([
        np.array([-8, -5, -2.5, 0, 2.5, 5, 7.5, 10, 12.5, 15, 18, 22, 27, 33, 40, 48, 57, 67, 78,
                  90, 105, 120, 140, 160, 185, 210, 240, 270, 305, 340, 380], dtype=float),
        np.arange(420.0, 1700.0, 25.0), np.arange(1700.0, 3000.0, 60.0),
        np.arange(3000.0, 4300.0, 150.0)])
    arazi = _grid_mesh("ARAZI", us, kara, arazi_z,
                       {"kumsal": lambda U, V, D: 1.0 - smooth(6.0, 10.0, D),
                        "orman": orman_maske}, M["arazi"], coll)
    deniz = np.array([5, 1, -1, -3, -5, -8, -11, -15, -20, -26, -33, -41, -50, -60, -72, -86,
                      -102, -122, -146, -175, -210, -255, -310, -380, -470, -580, -720, -900,
                      -1150, -1500, -2000, -2700, -3600], dtype=float)
    _grid_mesh("DENIZ", us, deniz, lambda U, V, D: np.full_like(U, -0.25),
               {"kiyi": lambda U, V, D: np.clip(-D / 55.0, 0.0, 1.0) ** 0.7}, M["deniz"], coll)
    return arazi


def _rv_soket(node, ad, tip):
    return [s for s in node.inputs if s.name == ad and s.type == tip][0]


def orman_gn(arazi_ob, kaynak):
    """Tepelere Geometry Nodes ile ağaç dağıt (yamaç yüzeyine oturur, 'orman' maskesi)."""
    ng = bpy.data.node_groups.new("YALOVA_ORMAN", 'GeometryNodeTree')
    ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, L = ng.nodes, ng.links
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    att = n.new("GeometryNodeInputNamedAttribute")
    att.data_type = 'FLOAT'
    att.inputs["Name"].default_value = "orman"
    yog = n.new("ShaderNodeMath")
    yog.operation = 'MULTIPLY'
    yog.inputs[1].default_value = ORMAN_YOGUNLUK
    dag = n.new("GeometryNodeDistributePointsOnFaces")
    dag.distribute_method = 'RANDOM'
    ci = n.new("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = kaynak
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    secim = n.new("FunctionNodeRandomValue")
    secim.data_type = 'INT'
    _rv_soket(secim, "Min", 'INT').default_value = 0
    _rv_soket(secim, "Max", 'INT').default_value = len(kaynak.children) - 1
    don = n.new("FunctionNodeRandomValue")
    don.data_type = 'FLOAT_VECTOR'
    _rv_soket(don, "Min", 'VECTOR').default_value = (0.0, 0.0, 0.0)
    _rv_soket(don, "Max", 'VECTOR').default_value = (0.08, 0.08, 6.283)
    olc = n.new("FunctionNodeRandomValue")
    olc.data_type = 'FLOAT'
    _rv_soket(olc, "Min", 'VALUE').default_value = 0.9
    _rv_soket(olc, "Max", 'VALUE').default_value = 1.7
    iop = n.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    bir = n.new("GeometryNodeJoinGeometry")
    L.new(gi.outputs[0], dag.inputs["Mesh"])
    L.new([s for s in att.outputs if s.type == 'VALUE'][0], yog.inputs[0])
    L.new(yog.outputs[0], dag.inputs["Density"])
    L.new(dag.outputs["Points"], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])
    L.new([s for s in secim.outputs if s.type == 'INT'][0], iop.inputs["Instance Index"])
    L.new([s for s in don.outputs if s.type == 'VECTOR'][0], iop.inputs["Rotation"])
    L.new([s for s in olc.outputs if s.type == 'VALUE'][0], iop.inputs["Scale"])
    L.new(gi.outputs[0], bir.inputs[0])
    L.new(iop.outputs[0], bir.inputs[0])
    L.new(bir.outputs[0], go.inputs[0])
    mod = arazi_ob.modifiers.new("ORMAN", 'NODES')
    mod.node_group = ng
    return mod


# ============================== YERLEŞİM ==============================
def _kenar_u(poly, v, taraf):
    xs = []
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 - v) * (y2 - v) <= 0 and y1 != y2:
            xs.append(x1 + (v - y1) / (y2 - y1) * (x2 - x1))
    return min(xs) if taraf < 0 else max(xs)


def _kenar_v(poly, u, taraf):
    ys = []
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (x1 - u) * (x2 - u) <= 0 and x1 != x2:
            ys.append(y1 + (u - x1) / (x2 - x1) * (y2 - y1))
    return min(ys) if taraf < 0 else max(ys)


def _icinde(poly, x, y):
    ic = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) / (y2 - y1) * (x2 - x1):
            ic = not ic
    return ic


def yerlesim():
    """Her parsel 2 sıra: 7104 -> 7+7 hizalı (ortada deniz aksı), 7105 -> 7 + 6 şaşırtmalı."""
    W2, D2 = B_W / 2, B_D / 2
    g_ext = D2 + TERAS_D + 0.15 - CIKMA_ON          # çekme hattına kadar güney uzantı
    k_ext = D2 + CEK_C                              # kuzey uzantı (çekirdek)
    bloklar = []
    for pid, poly, kolonlar in (("7104", P7104, ((-1, 7, 0.0), (1, 7, 0.0))),
                                ("7105", P7105, ((-1, 7, 0.0), (1, 6, 0.5)))):
        u_ref = {t: _kenar_u(poly, 0.0, t) - t * (CEKME_YAN + W2) for t in (-1, 1)}
        v_g = max(_kenar_v(poly, u_ref[t] + d, -1) for t in (-1, 1) for d in (-W2, W2))
        v_k = min(_kenar_v(poly, u_ref[t] + d, 1) for t in (-1, 1) for d in (-W2, W2))
        v0, v1 = v_g + CEKME_ON + g_ext, v_k - CEKME_ON - k_ext
        adim = (v1 - v0) / (max(n for _, n, _ in kolonlar) - 1)
        for taraf, adet, faz in kolonlar:
            for k in range(adet):
                v = v0 + (k + faz) * adim
                ks = [_kenar_u(poly, v + dv, taraf) for dv in (-D2 - TERAS_D, k_ext)]
                u = (max(ks) + CEKME_YAN + W2) if taraf < 0 else (min(ks) - CEKME_YAN - W2)
                harf = "A" if taraf < 0 else "B"
                bloklar.append(dict(ad=f"{pid}-{harf}{k + 1}", parsel=pid, kolon=taraf,
                                    u=u, v=v, adim=adim))
    return bloklar


def rapor(bloklar):
    D2 = B_D / 2
    en_az = 1e9
    for a in bloklar:
        for b in bloklar:
            if a is b or a["parsel"] != b["parsel"]:
                continue
            du = abs(a["u"] - b["u"]) - B_W
            dv = abs(a["v"] - b["v"]) - (D2 + TERAS_D + D2 + CEK_C)
            if du > 0 and dv > 0:
                m = math.hypot(du, dv)
            else:
                m = max(du, dv)
            en_az = min(en_az, m)
    taban = B_W * B_D + CEK_W * CEK_C
    brut = taban * KAT * len(bloklar)
    arsa = 5648.0 + 4510.0
    print("\n================ YALOVA ARMUTLU – 7104 / 7105 ================")
    print(f"Blok: {len(bloklar)}  |  Daire: {len(bloklar) * KAT * 2}  |  Bina yüksekliği: "
          f"{Z0 + KAT * KAT_H:.2f} m")
    print(f"Blok tabanı: {taban:.1f} m²  |  Brüt inşaat: {brut:,.0f} m²  |  "
          f"TAKS≈{taban * len(bloklar) / arsa:.2f}  KAKS≈{brut / arsa:.2f}")
    print(f"Daire brüt≈{(taban - CEK_W * 5.0) / 2:.0f} m² + teras  |  "
          f"Bloklar arası en dar mesafe: {en_az:.1f} m")
    print("==============================================================\n")


# ============================== PEYZAJ ==============================
def _kenar_parcalari(poly, iceri, bosluk_u=None, bosluk_w=6.0):
    """Parsel kenarlarını içe kaydırıp çizgi parçası olarak döndürür; kuzey kenarda giriş boşluğu."""
    n = len(poly)
    kuzey_i = max(range(n), key=lambda i: poly[i][1] + poly[(i + 1) % n][1])
    parcalar = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        nx, ny = _sol_normal(a, b)
        a2, b2 = (a[0] + nx * iceri, a[1] + ny * iceri), (b[0] + nx * iceri, b[1] + ny * iceri)
        if i == kuzey_i and bosluk_u is not None:
            dx, dy = b2[0] - a2[0], b2[1] - a2[1]
            t0 = (bosluk_u - bosluk_w / 2 - a2[0]) / dx
            t1 = (bosluk_u + bosluk_w / 2 - a2[0]) / dx
            t0, t1 = sorted((t0, t1))
            if 0 < t0 < t1 < 1:
                parcalar.append([a2, (a2[0] + dx * t0, a2[1] + dy * t0)])
                parcalar.append([(a2[0] + dx * t1, a2[1] + dy * t1), b2])
                continue
        parcalar.append([a2, b2])
    return parcalar


def peyzaj(M, coll, bloklar, agac, agac_coll):
    g = Govde()
    W2, D2 = B_W / 2, B_D / 2
    rnd = random.Random(TOHUM + 5)
    for pid, poly in (("7104", P7104), ("7105", P7105)):
        bl = [b for b in bloklar if b["parsel"] == pid]
        ua = [b["u"] for b in bl if b["kolon"] < 0]
        ub = [b["u"] for b in bl if b["kolon"] > 0]
        u_m = (sum(ua) / len(ua) + W2 + min(ub) - W2) / 2
        g.prizma(poly, 0.0, 0.04, M["cim"], alt=False)
        for p in _kenar_parcalari(poly, 0.15, u_m, 7.0):
            g.serit(p, 0.0, 0.55, 0.25, M["beyaz"])
        for p in _kenar_parcalari(poly, 0.95, u_m, 7.0):
            g.serit(p, 0.0, 1.25, 0.8, M["yesil"])
        vmin = min(b["v"] for b in bl) - D2 - TERAS_D - 2.5
        vmax = max(b["v"] for b in bl) + D2 + 3.5
        if pid == "7104":
            # deniz aksı: blok sıraları arasında denize uzanan yüzme kanalı + palmiyeler
            g.kutu(u_m - 3.2, u_m + 3.2, vmin, _kenar_v(poly, u_m, 1) - 0.5, 0.0, 0.06, M["tas"],
                   alt=False)
            va, vb = vmin + 3.0, vmax - 6.0
            g.kutu(u_m - 1.55, u_m + 1.55, va, va + 0.3, 0.0, 0.40, M["beyaz"])
            g.kutu(u_m - 1.55, u_m + 1.55, vb - 0.3, vb, 0.0, 0.40, M["beyaz"])
            g.kutu(u_m - 1.55, u_m - 1.25, va, vb, 0.0, 0.40, M["beyaz"])
            g.kutu(u_m + 1.25, u_m + 1.55, va, vb, 0.0, 0.40, M["beyaz"])
            g.kutu(u_m - 1.25, u_m + 1.25, va + 0.3, vb - 0.3, 0.0, 0.07, M["havuz"])
            g.kutu(u_m - 1.25, u_m + 1.25, va + 0.3, vb - 0.3, 0.07, 0.33, M["su"])
            vs = sorted({round(b["v"], 2) for b in bl})
            for v1, v2 in zip(vs[:-1], vs[1:]):
                vm = (v1 + v2) / 2
                for du in (-2.45, 2.45):
                    ornekle("palmiye", agac["AGAC_PALMIYE"], agac_coll, (u_m + du, vm, 0.06),
                            rnd.uniform(0, 6.28), rnd.uniform(0.9, 1.1))
            yol_u = u_m
            yol_w = 6.4
        else:
            # 7105: sıralar arası yürüyüş yolu + denize bakan havuz (güneydoğu köşe)
            dogu_bat = min(b["u"] for b in bl if b["kolon"] > 0) - W2
            bati_dog = max(ua) + W2
            yol_u, yol_w = (dogu_bat + bati_dog) / 2, 2.2
            g.kutu(yol_u - 1.1, yol_u + 1.1, vmin, _kenar_v(poly, yol_u, 1) - 0.5, 0.0, 0.06,
                   M["tas"], alt=False)
            b0 = min((b for b in bl if b["kolon"] > 0), key=lambda b: b["v"])
            ue = _kenar_u(poly, b0["v"] - 12, 1)
            pu0, pu1 = bati_dog + 4.2, ue - 3.2
            pv0 = _kenar_v(poly, pu1, -1) + 2.8
            pv1 = b0["v"] - D2 - TERAS_D - 1.6 - 1.4
            g.kutu(pu0 - 1.4, pu1 + 1.4, pv0 - 1.0, pv1 + 1.2, 0.0, 0.06, M["tas"], alt=False)
            g.kutu(pu0, pu1, pv0, pv0 + 0.3, 0.0, 0.25, M["beyaz"])
            g.kutu(pu0, pu1, pv1 - 0.3, pv1, 0.0, 0.25, M["beyaz"])
            g.kutu(pu0, pu0 + 0.3, pv0, pv1, 0.0, 0.25, M["beyaz"])
            g.kutu(pu1 - 0.3, pu1, pv0, pv1, 0.0, 0.25, M["beyaz"])
            g.kutu(pu0 + 0.3, pu1 - 0.3, pv0 + 0.3, pv1 - 0.3, 0.0, 0.07, M["havuz"])
            g.kutu(pu0 + 0.3, pu1 - 0.3, pv0 + 0.3, pv1 - 0.3, 0.07, 0.20, M["su"])
            for k in range(4):                      # havuz başı şezlongları
                x = pu0 + 1.2 + k * 2.6
                g.kutu(x - 0.32, x + 0.32, pv1 + 0.25, pv1 + 1.15, 0.06, 0.32, M["minder"])
            for k in range(3):
                ornekle("palmiye", agac["AGAC_PALMIYE"], agac_coll,
                        (pu1 + 0.6, pv0 + (pv1 - pv0) * k / 2, 0.06), rnd.uniform(0, 6.28), 0.95)
        # blok girişlerinden ana yola bağlantı
        for b in bl:
            vy = b["v"] + D2 + 2.0
            ua_, ub_ = sorted((b["u"], yol_u - math.copysign(yol_w / 2, yol_u - b["u"])))
            g.kutu(ua_ - 0.9, ub_ + 0.9, vy - 0.9, vy + 0.9, 0.0, 0.055, M["tas"], alt=False)
        # blok araları: zeytin / servi
        for b in bl:
            vm = b["v"] + b["adim"] / 2
            if vm + 6 > vmax:
                continue
            dis = b["u"] + b["kolon"] * (W2 + 1.2)
            tip = "AGAC_ZEYTIN" if rnd.random() < 0.7 else "AGAC_SERVI"
            ornekle(tip.lower(), agac[tip], agac_coll, (dis, vm, 0.04), rnd.uniform(0, 6.28),
                    rnd.uniform(0.85, 1.15))
    return g.obje("PEYZAJ", coll)


# ============================== ÇEVRE ==============================
def _yol_listesi():
    yollar = [
        ([(-0.45, -95), (-0.45, 440)], 7.6, "proje"),                  # Handere 1 Sk. (parseller arası)
        ([(-44.2, -125), (-44.2, 440)], 7.6, "proje"),                 # Handere 2 Sk.
        ([(42.6, -72), (32.0, 210), (31.0, 440)], 7.6, "proje"),      # Samanyolu Sk.
        ([(-430, 80.3), (44.0, 80.3)], 7.6, "proje"),                  # parsellerin kuzeyi
        (SAHIL_YOLU, 8.0, "sahil"),
        (ZAFER_CD, 11.0, "cadde"),
    ]
    for k in list(range(-9, -1)) + list(range(2, 12)):
        u = -0.45 + 44.2 * k
        v0 = _sahil_v(u)
        yollar.append(([(u, -400.0 if v0 is None else v0), (u, 460)], 7.0, "sokak"))
    for v in (175.0, 270.0):
        yollar.append(([(-700, v), (800, v)], 7.0, "sokak"))
    return yollar


def _kirp(pts, dmin=14.0, dmax=395.0, adim=4.0):
    """Çizgiyi kıyıdan sonra / tepelerden önce kalan en uzun parçaya kırp."""
    yog = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / adim))
        yog += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    yog.append(pts[-1])
    en, cur = [], []
    for p in yog:
        if dmin < float(kiyi_d(p[0], p[1])) < dmax and abs(p[0]) < 640:
            cur.append(p)
        else:
            if len(cur) > len(en):
                en = cur
            cur = []
    if len(cur) > len(en):
        en = cur
    return en


def _nokta_cizgi(px, py, pts):
    best = 1e9
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
        best = min(best, math.hypot(px - ax - t * dx, py - ay - t * dy))
    return best


def _yol_mesafe(x, y, kirpik, haric=None):
    """En yakın yol kenarına mesafe (yol içindeyse negatif)."""
    best = 1e9
    for p, gen, bb, _ in kirpik:
        if p is haric or not (bb[0] - 25 < x < bb[1] + 25 and bb[2] - 25 < y < bb[3] + 25):
            continue
        best = min(best, _nokta_cizgi(x, y, p) - gen / 2)
    return best


def _sahil_v(u):
    xs = [p[0] for p in SAHIL_YOLU]
    if u < xs[0] or u > xs[-1]:
        return None
    return float(np.interp(u, xs, [p[1] for p in SAHIL_YOLU]))


def _tekneler(M, coll):
    t = Govde()
    for (u, v, r, L) in ((25.0, -150.0, 0.5, 12.0), (112.0, -106.0, -0.4, 9.0),
                         (-20.0, -162.0, 1.0, 14.0), (-75.0, -188.0, 2.4, 7.0)):
        c, s = math.cos(r), math.sin(r)
        rot = lambda P: [(u + x * c - y * s, v + x * s + y * c) for x, y in P]
        t.prizma(rot([(-L / 2, -1.4), (L * 0.25, -1.5), (L / 2, 0.0), (L * 0.25, 1.5), (-L / 2, 1.4)]),
                 -0.5, 0.6, M["tekne"])
        t.prizma(rot([(-L * 0.45, -1.2), (L * 0.2, -1.25), (L * 0.42, 0.0), (L * 0.2, 1.25),
                      (-L * 0.45, 1.2)]), 0.6, 0.65, M["ahsap"])
        t.prizma(rot([(-L * 0.3, -0.95), (L * 0.12, -0.95), (L * 0.12, 0.95), (-L * 0.3, 0.95)]),
                 0.65, 1.15, M["tekne"])
        t.prizma(rot([(-L * 0.31, -0.97), (L * 0.13, -0.97), (L * 0.13, 0.97), (-L * 0.31, 0.97)]),
                 1.15, 1.45, M["araba_cam"])
        t.prizma(rot([(-L * 0.33, -1.0), (L * 0.1, -1.0), (L * 0.1, 1.0), (-L * 0.33, 1.0)]),
                 1.45, 1.55, M["tekne"])
    t.obje("TEKNELER", coll)


def _plaj(M, coll, rnd):
    """Kumsal: şemsiyeler, şezlonglar, havlular, güneşlenen/yürüyen insanlar, yüzücüler."""
    g = Govde()
    for _ in range(46):
        u = rnd.uniform(-165.0, 175.0)
        d = rnd.uniform(3.0, 8.5)
        x, y = kiyi_nokta(u, d)
        z = kumsal_z(d)
        g._t = rnd.random()
        g.silindir((x, y, z - 0.2), (x, y, z + 2.35), 0.025, M["metal"], 6)
        g.koni(x, y, z + 2.05, z + 2.45, rnd.uniform(0.95, 1.15), M["semsiye"], 10)
        a = rnd.uniform(0, math.pi)
        ca, sa = math.cos(a), math.sin(a)
        for k in range(rnd.choice((0, 1, 2, 2))):
            ox, oy = x + (k - 0.5) * 0.9 * -sa, y + (k - 0.5) * 0.9 * ca
            R = Matrix.Rotation(a, 3, 'Z')
            g.kutu_m((ox, oy, z + 0.28), (0.95, 0.32, 0.05), R, M["minder"])
            if rnd.random() < 0.6:
                g._t = rnd.random()
                g.kutu_m((ox, oy, z + 0.42), (0.8, 0.2, 0.1), R, M["ten"])
                g.kure((ox + ca * 0.9, oy + sa * 0.9, z + 0.45), (0.11, 0.11, 0.11), M["ten"], 8, 5)
    for _ in range(36):                             # havluda yatanlar
        u = rnd.uniform(-165.0, 175.0)
        d = rnd.uniform(2.0, 9.0)
        x, y = kiyi_nokta(u, d)
        z = kumsal_z(d)
        R = Matrix.Rotation(rnd.uniform(0, math.pi), 3, 'Z')
        g._t = rnd.random()
        g.kutu_m((x, y, z + 0.005), (0.95, 0.45, 0.01), R, M["kumas"])
        g.kutu_m((x, y, z + 0.12), (0.78, 0.2, 0.1), R, M["ten"])
    for _ in range(40):                             # yürüyenler / ayakta duranlar
        u = rnd.uniform(-160.0, 175.0)
        d = rnd.uniform(-1.0, 10.0) if rnd.random() < 0.75 else rnd.uniform(15.5, 18.5)
        x, y = kiyi_nokta(u, d)
        z = kumsal_z(d) if d < 14 else 0.42
        g._t = rnd.random()
        g.silindir((x, y, z), (x, y, z + 0.85), 0.13, M["ten"], 8)
        g.silindir((x, y, z + 0.85), (x, y, z + 1.45), 0.17, M["kumas"], 8)
        g.kure((x, y, z + 1.6), (0.11, 0.11, 0.12), M["ten"], 8, 5)
    for _ in range(18):                             # denizdekiler
        u = rnd.uniform(-150.0, 170.0)
        x, y = kiyi_nokta(u, -rnd.uniform(4.0, 30.0))
        g.kure((x, y, -0.2), (0.13, 0.13, 0.13), M["ten"], 8, 5)
    g.obje("PLAJ", coll, ton_attr=True)


def _sahil_promenat(M, yol, rnd):
    """Yükseltilmiş sahil yürüyüş yolu, taş parapet, aydınlatma ve banklar."""
    us = np.arange(-172.0, 302.0, 3.0)
    yurume = [kiyi_nokta(float(u), 17.0) for u in us]
    yol.serit(yurume, 0.0, 0.42, 4.2, M["tas"])
    yol.serit([kiyi_nokta(float(u), 14.95) for u in us], 0.0, 0.95, 0.3, M["tas"])
    for (x, y), t in _cizgi_boyunca([kiyi_nokta(float(u), 18.7) for u in us], 20.0):
        yol.silindir((x, y, 0.42), (x, y, 4.6), 0.06, M["metal"], 8)
        R = Matrix.Rotation(math.atan2(t[1], t[0]), 3, 'Z')
        yol.kutu_m((x, y, 4.62), (0.28, 0.10, 0.05), R, M["metal"])
    for (x, y), t in _cizgi_boyunca([kiyi_nokta(float(u), 15.9) for u in us], 13.0):
        R = Matrix.Rotation(math.atan2(t[1], t[0]), 3, 'Z')
        yol.kutu_m((x, y, 0.86), (0.9, 0.22, 0.03), R, M["ahsap"])
        yol.kutu_m((x, y, 0.64), (0.8, 0.12, 0.22), R, M["metal"])


def _cizgiler(yol, p, M, z, aralik=9.0, boy=3.0):
    for (x, y), t in _cizgi_boyunca(p, aralik):
        yol.kutu_m((x, y, z), (boy / 2, 0.07, 0.004), Matrix.Rotation(math.atan2(t[1], t[0]), 3, 'Z'),
                   M["cizgi"])


def _arabalar(kirpik, tipler, coll, rnd, cam_xy):
    """Sokaklarda park etmiş, sahil yolunda seyreden araçlar."""
    merkez = (0.0, -5.0)
    sayi = 0
    for p, gen, bb, tur in kirpik:
        for (x, y), t in _cizgi_boyunca(p, rnd.uniform(6.0, 8.5)):
            if math.hypot(x - merkez[0], y - merkez[1]) > 470:
                continue
            nx, ny = -t[1], t[0]
            if tur == "sahil":
                seritler = [(-1.9, 0.08), (1.9, 0.08), (-gen / 2 - 1.3, 0.35)]
            elif tur == "proje":
                seritler = [(-gen / 2 + 2.8, 0.30)]
            else:
                seritler = [(-gen / 2 + 1.1, 0.30), (gen / 2 - 1.1, 0.30)]
            for ofs, olas in seritler:
                if rnd.random() > olas:
                    continue
                cx, cy = x + nx * ofs, y + ny * ofs
                if _yol_mesafe(cx, cy, kirpik, haric=p) < 2.5:
                    continue                          # kavşak
                if any(_icinde(poly, cx, cy) for poly in (P7104, P7105)):
                    continue
                if math.hypot(cx - cam_xy[0], cy - cam_xy[1]) < 62:
                    continue
                # sağdan akan trafik: yolun sağındaki araç ileri, solundaki geri bakar
                ters = (ofs > 0) != (tur != "sahil" and rnd.random() < 0.15)
                yon = math.atan2(t[1], t[0]) + (math.pi if ters else 0.0)
                ornekle("araba", rnd.choice(tipler), coll, (cx, cy, 0.03), yon)
                sayi += 1
    return sayi


def cevre(M, coll, agac, agac_coll, arac_tipleri, cam_xy):
    rnd = random.Random(TOHUM)
    yol = Govde()
    kirpik = []
    for i, (pts, gen, tur) in enumerate(_yol_listesi()):
        p = _kirp(pts)
        if len(p) < 2:
            continue
        p = p[::3] + ([p[-1]] if (len(p) - 1) % 3 else [])
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        kirpik.append((p, gen, (min(xs), max(xs), min(ys), max(ys)), tur))
        z = 0.020 + 0.0004 * i
        yol.yatay_serit(p, gen, z, M["asfalt"])
        if tur in ("sahil", "cadde") or (tur == "proje" and gen > 7.5):
            _cizgiler(yol, p, M, z + 0.004)
    # proje parsellerinin çevresinde kaldırım
    for poly in (P7104, P7105):
        for p in _kenar_parcalari(poly, -0.85):
            yol.serit(p, 0.0, 0.14, 1.7, M["kaldirim"])
    _sahil_promenat(M, yol, rnd)
    for u in np.arange(-150.0, 160.0, 13.0):
        v = _sahil_v(u)
        if v is not None:
            ornekle("palmiye", agac["AGAC_PALMIYE"], agac_coll, (u, v - 6.5, 0.0),
                    rnd.uniform(0, 6.28), rnd.uniform(0.85, 1.15))
    for (a, b) in ISKELELER:
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy)
        a2 = (a[0] - dx / l * 10, a[1] - dy / l * 10)
        yol.serit([a2, b], -1.2, 0.35, 3.2, M["iskele"])
        for s in (-1.5, 1.5):
            yol.serit([(a2[0] - dy / l * s, a2[1] + dx / l * s), (b[0] - dy / l * s, b[1] + dx / l * s)],
                      0.35, 1.3, 0.05, M["metal"])
    yol.obje("YOLLAR_SAHIL", coll)
    _tekneler(M, coll)
    _plaj(M, coll, rnd)

    ev, cati, ek = Govde(), Govde(), Govde()

    def ev_ekle(x0, x1, y0, y1, kat_say, kirma=True, bosluk=2.5):
        H = 3.0 * kat_say + 0.3
        ev._t = cati._t = ek._t = rnd.random()
        w, d = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ev.kutu(x0, x1, y0, y1, 0.0, H, M["ev_duvar"], ust=False if kirma else None, alt=False)
        if kirma:
            rh = min(w, d) * 0.28
            cati.kirma_cati(x0, x1, y0, y1, H, rh, M["ev_cati"])
            tepe = H + rh
        else:
            ev.kutu(x0 + 0.25, x1 - 0.25, y0 + 0.25, y1 - 0.25, H, H + 0.04, M["duz_cati"], alt=False)
            for (a0, a1, b0, b1) in ((x0, x1, y0, y0 + 0.2), (x0, x1, y1 - 0.2, y1),
                                     (x0, x0 + 0.2, y0, y1), (x1 - 0.2, x1, y0, y1)):
                ev.kutu(a0, a1, b0, b1, H, H + 0.6, M["ev_duvar"], alt=False)
            tepe = H
            if rnd.random() < 0.6:                    # su deposu
                tx, ty = x0 + 1.3, y1 - 1.3
                ek.silindir((tx, ty, H), (tx, ty, H + 1.1), 0.55,
                            M["tank_siyah" if rnd.random() < 0.5 else "tank"], 10)
        # güneş enerjili su ısıtıcı: Türkiye çatılarının imzası
        if rnd.random() < 0.62:
            for k in range(1 if rnd.random() < 0.7 else 2):
                px = cx + (k - 0.5) * 2.3 * (1 if k else 0) + rnd.uniform(-0.8, 0.8)
                py = cy + rnd.uniform(-1.0, 0.6)
                pz = (tepe - 0.2) if kirma else (H + 0.35)
                R = Matrix.Rotation(math.radians(40), 3, 'X')
                ek.kutu_m((px, py, pz + 0.5), (1.0, 0.5, 0.03), R, M["gunes_panel"])
                tz, ty = pz + 0.5 + 0.55, py + 0.5
                ek.silindir((px - 0.85, ty, tz), (px + 0.85, ty, tz), 0.27, M["tank"], 10)
                for sx in (-0.8, 0.8):
                    ek.kutu(px + sx - 0.03, px + sx + 0.03, py - 0.4, py - 0.34, pz - 0.2, pz + 0.3,
                            M["metal"])
        # balkonlar (denize bakan -Y cephesi) ve tente
        if kat_say >= 2 and rnd.random() < 0.75:
            bw = w * rnd.uniform(0.45, 0.75)
            bx0 = cx - bw / 2 + rnd.uniform(-0.6, 0.6)
            for f in range(1, kat_say):
                zf = 3.0 * f + 0.15
                ev.kutu(bx0, bx0 + bw, y0 - 1.25, y0, zf - 0.15, zf, M["ev_duvar"])
                ek.kutu(bx0, bx0 + bw, y0 - 1.25, y0 - 1.19, zf, zf + 1.0, M["demir"])
                ek.kutu(bx0, bx0 + 0.06, y0 - 1.25, y0, zf, zf + 1.0, M["demir"])
                ek.kutu(bx0 + bw - 0.06, bx0 + bw, y0 - 1.25, y0, zf, zf + 1.0, M["demir"])
                if f == kat_say - 1 and rnd.random() < 0.4:
                    ek.kutu_m((bx0 + bw / 2, y0 - 0.75, zf + 2.55), (bw / 2, 0.8, 0.02),
                              Matrix.Rotation(math.radians(-18), 3, 'X'), M["tente"])
        if rnd.random() < 0.35:                       # çanak anten
            ax, ay = x1 - 0.8, y0 + 0.8
            ek.silindir((ax, ay, tepe - 0.3), (ax, ay - 0.1, tepe + 0.05), 0.38, M["tank"], 10)
        if bosluk > 0.6:                              # bahçe duvarı (ön tarafta kapı boşluğu)
            m_ = min(bosluk - 0.3, 3.0)
            bx0_, bx1_, by0_, by1_ = x0 - m_, x1 + m_, y0 - m_, y1 + m_
            ek.kutu(bx0_, cx - 1.6, by0_, by0_ + 0.22, 0.0, 0.95, M["bahce_duvar"])
            ek.kutu(cx + 1.6, bx1_, by0_, by0_ + 0.22, 0.0, 0.95, M["bahce_duvar"])
            ek.kutu(bx0_, bx1_, by1_ - 0.22, by1_, 0.0, 0.95, M["bahce_duvar"])
            ek.kutu(bx0_, bx0_ + 0.22, by0_, by1_, 0.0, 0.95, M["bahce_duvar"])
            ek.kutu(bx1_ - 0.22, bx1_, by0_, by1_, 0.0, 0.95, M["bahce_duvar"])
        return (x0, x1, y0, y1)

    # Samanyolu Sk. doğusundaki mevcut sıra yazlıklar
    evler = []
    v = -50.0
    while v < 72:
        ue = _kenar_u(P7105, min(max(v, -64.0), 73.0), 1) + 9.0
        kay = 0.8 if int((v + 50) / 7.6) % 2 else 0.0
        evler.append(ev_ekle(ue + kay, ue + kay + 11.0, v, v + 7.3, 2, bosluk=0.0))
        v += 7.6

    # komşu dokusu: sokak ızgarasına oturan parseller
    agac_tur = ("AGAC_YUVARLAK", "AGAC_ZEYTIN", "AGAC_SERVI", "AGAC_YUVARLAK", "AGAC_CAM")
    lots = []
    for k in range(-9, 12):
        for su in (12.8, 31.4):                           # sokaklar arası iki parsel
            uc = -0.45 + 44.2 * k + su
            for vc in np.arange(-190.0, 450.0, 21.0):
                lots.append((uc + rnd.uniform(-1.5, 1.5), float(vc) + rnd.uniform(-2, 2)))
    for (uc, vc) in lots:
        if -52 < uc < 95 and vc < 88:                     # proje + sıra evler + boş tarla
            continue
        d = float(kiyi_d(uc, vc))
        if d < 42 or d > 390:
            continue
        sv = _sahil_v(uc)
        if sv is not None and vc < sv + 9:
            continue
        w, dd = rnd.uniform(8.5, 12.5), rnd.uniform(8.5, 12.0)
        r_ic = math.hypot(w, dd) / 2
        bos = _yol_mesafe(uc, vc, kirpik) - r_ic
        if bos < 1.0:
            continue
        if rnd.random() < 0.28:
            for _ in range(rnd.randint(2, 5)):
                ornekle("agac", agac[rnd.choice(agac_tur)], agac_coll,
                        (uc + rnd.uniform(-6, 6), vc + rnd.uniform(-6, 6), 0.0),
                        rnd.uniform(0, 6.28), rnd.uniform(0.7, 1.2))
            continue
        evler.append(ev_ekle(uc - w / 2, uc + w / 2, vc - dd / 2, vc + dd / 2,
                             rnd.choice((2, 2, 3, 3, 4)), rnd.random() < 0.78, bos))
        for _ in range(rnd.choice((1, 1, 2, 2, 3))):
            ku = uc + math.copysign(w / 2 + rnd.uniform(1.6, 2.8), rnd.uniform(-1, 1))
            ornekle("agac", agac[rnd.choice(agac_tur)], agac_coll, (ku, vc + rnd.uniform(-5, 5), 0.0),
                    rnd.uniform(0, 6.28), rnd.uniform(0.7, 1.15))
    ev.obje("KOMSU_EVLER", coll, ton_attr=True)
    cati.obje("KOMSU_CATILAR", coll, ton_attr=True)
    ek.obje("KOMSU_DETAYLAR", coll, ton_attr=True)

    # sahil parkı ve proje güneyi: dağınık ağaçlar
    for _ in range(140):
        u = rnd.uniform(-180, 300)
        d = rnd.uniform(20, 70)
        v = float(kiyi_v(u)) + d
        sv = _sahil_v(u)
        if sv is not None and v > sv - 6:
            v = sv - rnd.uniform(8, 20)
            if float(kiyi_d(u, v)) < 21:
                continue
        tip = rnd.choice(("AGAC_YUVARLAK", "AGAC_ZEYTIN", "AGAC_PALMIYE", "AGAC_CAM"))
        ornekle("agac", agac[tip], agac_coll, (u, v, 0.0), rnd.uniform(0, 6.28),
                rnd.uniform(0.75, 1.15))
    n_araba = _arabalar(kirpik, arac_tipleri, coll, rnd, cam_xy)
    return len(evler), n_araba


# ============================== IŞIK / KAMERA / RENDER ==============================
def _gunes_yonu(el_derece=None):
    az = math.radians(GUNES_AZIMUT)
    el = math.radians(GUNES_YUKSEKLIK if el_derece is None else el_derece)
    e, n = math.sin(az), math.cos(az)                  # gerçek doğu / kuzey
    th = math.radians(KUZEY_SAPMA)
    u = e * math.cos(th) - n * math.sin(th)
    v = e * math.sin(th) + n * math.cos(th)
    return Vector((u * math.cos(el), v * math.cos(el), math.sin(el))).normalized()


def _hdri_dunya(nt, yol):
    """HDRI'daki güneşi bulur, gökyüzünü güneş azimutuna döndürür; güneş diskini kırpıp
    enerjisini ayrı güneş lambasına aktarır (temiz, keskin gölge)."""
    img = bpy.data.images.load(yol, check_existing=True)       # render için tam çözünürlük
    kopya = bpy.data.images.load(yol, check_existing=False)    # analiz için küçük kopya
    kopya.scale(1024, 512)
    W, H = kopya.size
    a = np.empty(W * H * 4, np.float32)
    kopya.pixels.foreach_get(a)
    bpy.data.images.remove(kopya)
    a = a.reshape(H, W, 4)[..., :3]
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    y0, x0 = np.unravel_index(int(np.argmax(lum)), lum.shape)
    C = max(4.0, float(np.percentile(lum, 99.7)) * 1.6)
    r = max(4, W // 90)
    satir = np.arange(max(0, y0 - r), min(H, y0 + r + 1))
    sutun = np.arange(x0 - r, x0 + r + 1) % W
    pen = a[satir][:, sutun]
    fazla = np.clip(pen - C, 0.0, None)
    el = ((satir + 0.5) / H - 0.5) * math.pi
    phi = 2 * math.pi * (0.5 - (sutun + 0.5) / W)
    dO = (2 * math.pi / W) * (math.pi / H) * np.cos(el)[:, None]
    E = (fazla * dO[..., None]).sum(axis=(0, 1))
    wgt = fazla.mean(-1) * dO
    yon = np.array([(wgt * np.cos(el)[:, None] * np.cos(phi)[None, :]).sum(),
                    (wgt * np.cos(el)[:, None] * np.sin(phi)[None, :]).sum(),
                    (wgt * np.sin(el)[:, None]).sum()])
    yon /= np.linalg.norm(yon)
    phi_s, el_s = math.atan2(yon[1], yon[0]), math.asin(float(yon[2]))
    hedef = _gunes_yonu(0.0)
    phi_t = math.atan2(hedef.y, hedef.x)
    k = HEDEF_GUNES / max(float(E.max()), 1e-3)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0.0, 0.0, phi_s - phi_t)
    et = nt.nodes.new("ShaderNodeTexEnvironment")
    et.image = img
    kirp = nt.nodes.new("ShaderNodeVectorMath")
    kirp.operation = 'MINIMUM'
    kirp.inputs[1].default_value = (C, C, C)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = k
    o = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], et.inputs["Vector"])
    nt.links.new(et.outputs["Color"], kirp.inputs[0])
    nt.links.new(_vmat(nt, 'MULTIPLY', kirp.outputs[0], GOK_TONU), bg.inputs["Color"])
    nt.links.new(bg.outputs[0], o.inputs[0])
    d = Vector((math.cos(el_s) * math.cos(phi_t), math.cos(el_s) * math.sin(phi_t), math.sin(el_s)))
    print(f"  HDRI güneşi: yükseklik {math.degrees(el_s):.1f}°, ışınım {E.max():.1f} -> {HEDEF_GUNES}")
    return d, tuple(float(x) for x in E / E.max())


def _gokyuzu_dunya(nt, d):
    sky = nt.nodes.new("ShaderNodeTexSky")
    for tip in ("MULTIPLE_SCATTERING", "NISHITA", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        try:
            sky.sky_type = tip
            break
        except Exception:
            pass
    for ad, deger in (("sun_disc", False), ("sun_elevation", math.radians(GUNES_YUKSEKLIK)),
                      ("sun_rotation", math.atan2(d.x, d.y)), ("altitude", 30.0),
                      ("air_density", 1.0), ("aerosol_density", 2.2), ("dust_density", 2.2),
                      ("ozone_density", 1.0)):
        try:
            setattr(sky, ad, deger)
        except Exception:
            pass
    if sky.sky_type == "HOSEK_WILKIE":
        sky.sun_direction = d
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 0.28
    o = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], o.inputs[0])


def isik(coll):
    w = bpy.data.worlds.new("YALOVA_GOKYUZU")
    if w.node_tree is None:
        w.use_nodes = True
    try:                                      # güneş ayrı lambada; gökyüzü için küçük harita yeter
        w.cycles.sampling_method = 'MANUAL'
        w.cycles.sample_map_resolution = 1024
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    d, gunes_rgb = None, (1.0, 1.0, 1.0)
    yol = ph_hdri()
    if yol:
        try:
            d, gunes_rgb = _hdri_dunya(nt, yol)
        except Exception as e:
            print("  HDRI kurulamadı, prosedürel gökyüzü:", e)
            nt.nodes.clear()
            d = None
    if d is None:
        d = _gunes_yonu()
        _gokyuzu_dunya(nt, d)
    ld = bpy.data.lights.new("GUNES", 'SUN')
    ld.energy = HEDEF_GUNES
    ld.angle = math.radians(0.6)
    rgb = [gunes_rgb[i] * GUNES_TONU[i] for i in range(3)]
    ld.color = tuple(c / max(rgb) for c in rgb)
    ob = bpy.data.objects.new("GUNES", ld)
    ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(ob)
    return w


def kamera(ad, konum, hedef, lens, coll):
    cd = bpy.data.cameras.new(ad)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start, cd.clip_end = 0.5, 15000.0
    ob = bpy.data.objects.new(ad, cd)
    ob.location = konum
    ob.rotation_euler = (Vector(hedef) - Vector(konum)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(ob)
    return ob


def _gpu_ac():
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except Exception:
        return False
    for tip in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = tip
        except Exception:
            continue
        try:
            prefs.refresh_devices()
        except Exception:
            try:
                prefs.get_devices()
            except Exception:
                pass
        if any(c.type == tip for c in prefs.devices):
            for c in prefs.devices:
                c.use = c.type == tip
            return True
    return False


def render_ayari(sc, coz, gpu):
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'GPU' if gpu else 'CPU'
    cy.samples = ORNEK
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces = 10, 3, 4
    cy.transmission_bounces, cy.transparent_max_bounces = 8, 16
    cy.caustics_reflective = cy.caustics_refractive = False
    cy.blur_glossy = 0.5
    cy.sample_clamp_indirect = 8.0
    sc.render.resolution_x, sc.render.resolution_y = coz
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '8'
    try:
        sc.view_settings.view_transform = 'AgX'
        for look in ("AgX - Medium High Contrast", "Medium High Contrast", "AgX - Base Contrast"):
            try:
                sc.view_settings.look = look
                break
            except Exception:
                pass
    except Exception:
        sc.view_settings.view_transform = 'Filmic'
    sc.view_settings.exposure = POZLAMA


# ============================== ANA AKIŞ ==============================
def kur():
    sc = sahneyi_temizle()
    sc.name = "YALOVA_GENEL"
    sc.unit_settings.system = 'METRIC'
    print("Poly Haven varlıkları:", VARLIK_KLASORU)
    dokulari_hazirla()
    M = malzemeler()

    # tip koleksiyonları sahneye bağlanmaz; örnekler (instance) üzerinden render'a girer
    # (düzenlemek için: Outliner > Blender File > Collections > TIP_BLOK)
    c_tip = bpy.data.collections.new("TIP_BLOK")
    c_agac_tip = bpy.data.collections.new("TIP_AGAC")
    c_arac_tip = bpy.data.collections.new("TIP_ARAC")
    c_proje = koleksiyon("PROJE_27_BLOK")
    c_peyzaj = koleksiyon("PEYZAJ")
    c_cevre = koleksiyon("CEVRE_DENIZ")
    c_kam = koleksiyon("KAMERA_ISIK")

    blok_tipi(M, c_tip)
    agac = agac_tipleri(M, c_agac_tip)
    araclar = araba_tipleri(M, c_arac_tip)
    bloklar = yerlesim()
    c_7104 = koleksiyon("PARSEL_7104", c_proje)
    c_7105 = koleksiyon("PARSEL_7105", c_proje)
    for b in bloklar:
        ornekle("BLOK_" + b["ad"], c_tip, c_7104 if b["parsel"] == "7104" else c_7105,
                (b["u"], b["v"], 0.0))

    # Kamera 1: denizden, güneydoğudan kuşbakışı – tüm proje
    cam1 = kamera("CAM_GENEL", (138.0, -221.0, 70.0), (22.4, -46.0, 0.0), 35.0, c_kam)
    # Kamera 2: denize en yakın, deniz aksına bakan blok (7104-B1) – tek blok
    hb = next(b for b in bloklar if b["ad"] == "7104-B1")
    cam2 = kamera("CAM_BLOK", (hb["u"] + 30.0, hb["v"] - 50.0, 25.0),
                  (hb["u"] - 1.5, hb["v"] + 0.5, 9.0), 55.0, c_kam)

    peyzaj(M, c_peyzaj, bloklar, agac, c_peyzaj)
    arazi = deniz_ve_arazi(M, c_cevre)
    orman_gn(arazi, agac["ORMAN"])
    ev_sayisi, arac_sayisi = cevre(M, c_cevre, agac, c_cevre, araclar, tuple(cam2.location.xy))
    rapor(bloklar)
    sc.world = isik(c_kam)

    # kamera dibindeki ağaçları kaldır (ön planda kaba görünmesin)
    for ob in list(c_cevre.objects) + list(c_peyzaj.objects):
        ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
        if ic and ic.name.startswith("AGAC") and \
                (ob.location.xy - cam2.location.xy).length < 42.0:
            bpy.data.objects.remove(ob, do_unlink=True)

    gpu = _gpu_ac()
    sc.camera = cam1
    render_ayari(sc, COZ_GENEL, gpu)
    sc2 = bpy.data.scenes.new("YALOVA_TEK_BLOK")
    for c in (c_proje, c_peyzaj, c_cevre, c_kam):
        sc2.collection.children.link(c)
    sc2.world = sc.world
    sc2.camera = cam2
    sc2.unit_settings.system = 'METRIC'
    render_ayari(sc2, COZ_BLOK, gpu)
    print(f"Komşu ev: {ev_sayisi}  |  Araç: {arac_sayisi}  |  Doku: {len(DOKU)}/{len(DOKULAR)}  |  "
          f"Render cihazı: {'GPU' if gpu else 'CPU'}")
    return sc, sc2


def render_al(sc, sc2):
    os.makedirs(CIKTI_KLASORU, exist_ok=True)
    for s, dosya in ((sc, "01_yalova_armutlu_genel.png"), (sc2, "02_yalova_armutlu_tek_blok.png")):
        s.render.filepath = os.path.join(CIKTI_KLASORU, dosya)
        bpy.ops.render.render(write_still=True, scene=s.name)
        print("Kaydedildi:", s.render.filepath)


if __name__ == "__main__":
    gc.disable()                         # yüz binlerce geometri listesi: kurulumu hızlandırır
    try:
        _sc, _sc2 = kur()
    finally:
        gc.enable()
    if OTOMATIK_RENDER:
        render_al(_sc, _sc2)
