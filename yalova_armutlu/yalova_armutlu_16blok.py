# -*- coding: utf-8 -*-
"""
YALOVA · ARMUTLU · KARŞIYAKA MAH. (Tavşantepe Mevkii, Pafta 39/2)
PARSEL 7104 (5.648 m²) + 7105 (4.510 m²)
13 BLOK (7104: 6 · 7105: 7) · ZEMİN+5 = 6 KAT · KATTA 4 DAİRE (2+1)  ->  312 DAİRE   (v4)

Blok tipleri: Katar Mühendislik Mimarlık T_P-4 kat planı (7104 ve 7105 tip planları, 264 m²);
blok konumları T_P-4 vaziyet planından. Kuzey ve güney yarıda ikişer daire, uçlarda balkonlu
salonlar, ortada asansör + merdiven, kuzeyde bina girişi nişi. Salon cephesinde Fransız cam,
balkon tarafında sürgülü cam, yatak odalarında 1,50 x 1,50 m pencere. Kat silmeleri #302B27;
diğer cephe malzemeleri v2 ile aynı.

Blender 4.2 – 5.x · Cycles (GPU önerilir)
Arayüzden : Scripting sekmesi > Open > bu dosya > Run Script
            İki sahne kurulur: "YALOVA_GENEL" (tüm proje) ve "YALOVA_TEK_BLOK" -> F12
Konsoldan : blender -b -P yalova_armutlu_16blok.py -- --render  [--cikti KLASOR] [--ornek N]
            [--cevrimdisi]  (internet kullanmadan, prosedürel malzemelerle)
            [--sol N] [--sag N]  (7104 / 7105 blok adedi; plandaki dizilim için --sol 9)
            [--yan]  (yalnız yan cephe görüntüsü)

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
COZ_BLOK = (2000, 1600)          # tek blok (5:4 yatay – blok geniş)
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

# Blok tipleri (m) – T_P-4 kat planından ölçüldü. Kat planı sayfaya sığdırılarak basıldığı için
# ölçek, vaziyet planındaki (1/500) blok dış ölçülerine oturtuldu. Katta 4 adet 2+1 (brüt 58 m²).
# x: parsel enine (doğu +), y: parsel boyuna (kuzey +, bina girişi kuzeyde). Sağ yarı verilir.
#   xb: balkon dış hattı        xs: dış duvar (salon | balkon)     xr: salon | yatak odası bandı
#   yu: uç bölge (salon + balkon) yarı derinliği    yo: yatak odası bandı yarı derinliği
#   nx, ny: giriş nişi yarı genişliği / nişin dibi  oy: yatak odalarının çekirdek tarafı
#   oda9, oda6: yatak odalarının x aralığı          bk: balkon cephesindeki dolu duvarın ucu
BLOK_TIPLERI = {
    "A264": dict(xb=12.92, xs=10.70, xr=7.04, yu=5.12, yo=5.61, nx=0.76, ny=2.80, oy=2.93,
                 oda9=(3.49, 6.89), oda6=(0.91, 3.40), bk=11.41, brut=264.0),      # 7104
    "B264": dict(xb=11.67, xs=9.65, xr=6.26, yu=6.15, yo=6.15, nx=1.17, ny=2.94, oy=2.95,
                 oda9=(3.41, 6.12), oda6=(1.33, 3.29), bk=10.16, brut=264.0),      # 7105
}
ODA_PENCERE = (1.50, 1.50, 0.90)  # yatak odası penceresi: genişlik, yükseklik, parapet
# Blok dizisi: her parselde tek sıra, A bloğu kuzeyde. İlk ve son bloğun merkezi T_P-4 vaziyet
# planından; aradakiler eşit aralıkla (planda 7104'te 9 blok var; seçilen düzen 6 + 7).
DIZI = {
    "7104": dict(tip="A264", adet=6, kuzey=(-22.36, 64.30), guney=(-20.86, -71.76)),
    "7105": dict(tip="B264", adet=7, kuzey=(18.39, 63.37), guney=(19.83, -54.54)),
}
KAT, KAT_H = 6, 3.10             # zemin + 5 normal kat, kattan kata
Z0 = 0.60                        # zemin kat döşeme kotu (+0.60)
DOSEME_T = 0.30                  # döşeme alnı
SILME = 0.25                     # kat silmesinin (döşeme alnı) cepheden taşması
R_KOSE = 1.10                    # balkon dış köşe yarıçapı
DUVAR_T = 0.25                   # dış duvar kalınlığı (pencere sövesi derinliği)
CAM_GERI = 0.10                  # camın dış yüzden içeri çekilmesi
ISIK_ORANI = 0.35                # akşamüstü ışığı yanan oda oranı (blok ve oda başına rastgele)
ISIK_RENK = (1.0, 0.70, 0.42)    # iç mekân ışığı (~2700 K)
KAHRAMAN = None                  # tek blok görselindeki blok (None: denize en yakın)

_ARG = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--render" in _ARG:
    OTOMATIK_RENDER = True
if "--onizleme" in _ARG:
    ORNEK, COZ_GENEL, COZ_BLOK = 24, (960, 540), (600, 480)
if "--cikti" in _ARG:
    CIKTI_KLASORU = _ARG[_ARG.index("--cikti") + 1]
if "--ornek" in _ARG:
    ORNEK = int(_ARG[_ARG.index("--ornek") + 1])
if "--cevrimdisi" in _ARG:
    POLYHAVEN = False
if "--sol" in _ARG:
    DIZI["7104"]["adet"] = int(_ARG[_ARG.index("--sol") + 1])
if "--sag" in _ARG:
    DIZI["7105"]["adet"] = int(_ARG[_ARG.index("--sag") + 1])
SADECE_YAN = "--yan" in _ARG

# =========================== PALET (sRGB HEX) ===========================
# Sancaktepe'de kullandığınız kodlar varsa bu satırlara birebir yazın; tüm sahne günceller.
PALET = {
    "beyaz":       "#ECE8E1",   # bahçe duvarı – sıcak beyaz kompozit
    "silme":       "#302B27",   # kat silmeleri (döşeme alınları), çatı saçağı – koyu kahve-antrasit
    "traverten":   "#CDBDA2",   # cephe kaplama – açık traverten
    "antrasit":    "#2C2E31",   # çekirdek kulesi, saksılar
    "kaide":       "#3D3A36",   # zemin kaidesi – bazalt
    "bronz":       "#8E6C49",   # doğrama, dikey fin, küpeşte – şampanya bronz
    "ahsap":       "#7B4A2B",   # teras tavanları, saçak altı – tik
    "cam":         "#C9D8D4",   # cephe camı – geçirgenlik tonu (hafif yeşil füme)
    "perde":       "#DED5C4",   # cam arkası tül perde
    "korkuluk":    "#E4F2EE",   # çerçevesiz cam korkuluk
    "tas":         "#D9D1C3",   # teras / peyzaj taşı
    "minder":      "#EEEAE3",   # şezlong minderi
    "yesil":       "#4C6B2E",   # çit, saksı bitkisi
    "cati":        "#BDB6AA",   # çatı – açık gri çakıl
    "cim":         "#6F8F3A",
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
        self._oz = []            # (ilk yüz, {ad: değer}): yüz öznitelikleri (oda, perde ölçüleri)

    def ozellik(self, **kw):
        """Bundan sonra eklenen yüzlerin öznitelikleri (verilmeyenler 0)."""
        self._oz.append((len(self.f), kw))

    def dortgen(self, pts, mat):
        b = len(self.v)
        self._v(list(pts))
        self.yuz(range(b, b + len(pts)), mat)

    def kutu6(self, x0, x1, y0, y1, z0, z1, m):
        """Yüz başına malzemeli kutu: m = {'-x','+x','-y','+y','-z','+z': malzeme, 'v': varsayılan};
        None verilen yüz oluşturulmaz."""
        b = len(self.v)
        self._v([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                 (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
        for k, q in (("-z", (0, 3, 2, 1)), ("+z", (4, 5, 6, 7)), ("-y", (0, 1, 5, 4)),
                     ("+y", (2, 3, 7, 6)), ("-x", (3, 0, 4, 7)), ("+x", (1, 2, 6, 5))):
            mat = m.get(k, m.get("v"))
            if mat is not None:
                self.yuz([b + i for i in q], mat)

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
        n = len(self.f)
        for ad in sorted({k for _, kw in self._oz for k in kw}):
            deg = [0.0] * n
            for j, (ilk, kw) in enumerate(self._oz):
                son = self._oz[j + 1][0] if j + 1 < len(self._oz) else n
                if ad in kw:
                    deg[ilk:son] = [float(kw[ad])] * (son - ilk)
            a = me.attributes.new(ad, 'FLOAT', 'FACE')
            a.data.foreach_set("value", deg)
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


def mat_cam_ince(hexr):
    """İnce mimari cam: Fresnel'e göre gökyüzü yansıması, arkasındaki oda görünür;
    güneş ve gölge ışınları içeri geçer."""
    m, nt, out = _yeni_mat("Cephe_Cami")
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.52
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (*renk(hexr), 1.0)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (0.90, 0.95, 0.96, 1.0)
    _ata(gl, 0.015, "Roughness")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_aralik(nt, fr.outputs[0], 0.0, 1.0, 0.11, 1.0), mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(gl.outputs[0], mx.inputs[2])
    _golge_seffaf(nt, out, mx.outputs[0])
    return m


def _rastgele(nt, ad="oda", ofset=0.0):
    """Yüz özniteliği (oda / pencere kimliği) ve blok örneğine göre değişen 0-1 rastgele sayı."""
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = ad
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(at.outputs["Fac"], cb.inputs[0])
    nt.links.new(oi.outputs["Random"], cb.inputs[1])
    cb.inputs[2].default_value = ofset
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = '3D'
    nt.links.new(cb.outputs[0], wn.inputs["Vector"])
    return wn.outputs["Value"]


def _secim(nt, r, renkler):
    """0-1 sayıyla paletten renk seç (sabit geçişli rampa)."""
    c = _rampa(nt, r, [(i / len(renkler), rr) for i, rr in enumerate(renkler)])
    c.node.color_ramp.interpolation = 'CONSTANT'
    return c


def _isik_acik(nt):
    """Oda ışığı yanıyor mu (0/1): oda ve blok başına rastgele, oran ISIK_ORANI."""
    return _matematik(nt, 'GREATER_THAN', _rastgele(nt, "oda", 3.7), 1.0 - ISIK_ORANI)


def _oz_isik(nt, p, guc):
    _ata(p, (*ISIK_RENK, 1.0), "Emission Color", "Emission")
    nt.links.new(_matematik(nt, 'MULTIPLY', _isik_acik(nt), guc), _ata(p, 0.0, "Emission Strength"))


def mat_ic(ad, renkler, rough=0.8, isik=0.0, ofset=0.0, spec=0.3, coat=0.0):
    """İç mekân yüzeyi: oda + blok başına paletten renk; ışığı yanan odada sıcak öz-ışıma."""
    m, nt, out = _yeni_mat(ad)
    p = _bsdf(nt, renkler[0], rough, spec=spec, coat=coat)
    if len(renkler) > 1:
        nt.links.new(_secim(nt, _rastgele(nt, "oda", ofset), renkler), p.inputs["Base Color"])
    if isik > 0:
        _oz_isik(nt, p, isik)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_parke():
    """Parke: oda başına ton (açık meşe / bal meşe / ceviz / gri taş), tahta damarı, hafif parlak."""
    m, nt, out = _yeni_mat("Ic_Parke")
    p = _bsdf(nt, renk("#B08F68"), 0.36, spec=0.45)
    taban = _secim(nt, _rastgele(nt, "oda", 9.1), [renk("#C4A47E"), renk("#A9825A"),
                                                   renk("#6E4B33"), renk("#BDB5A9")])
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    _ata(wv, 5.0, "Scale"); _ata(wv, 7.0, "Distortion"); _ata(wv, 3.0, "Detail")
    nt.links.new(_koord(nt), wv.inputs["Vector"])
    nt.links.new(_olcekle(nt, taban, _aralik(nt, wv.outputs["Fac"], 0.0, 1.0, 0.82, 1.12)),
                 p.inputs["Base Color"])
    _oz_isik(nt, p, 0.18)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_lamba():
    """Abajur / sarkıt: ışığı yanan odada parlak sıcak ışık, sönükken krem kumaş."""
    m, nt, out = _yeni_mat("Lamba")
    p = _bsdf(nt, renk("#EFE6D6"), 0.7, spec=0.3)
    _oz_isik(nt, p, 9.0)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_perde():
    """Perde: pencere (yüz öznitelikleri) ve blok başına rastgele – yanlara toplanmış ya da yarı
    çekili fon perde, çekili tül, yarı inik stor; kıvrımlı, arkadan ışığı geçiren kumaş."""
    m, nt, out = _yeni_mat("Perde")

    def oz(ad):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = ad
        return a.outputs["Fac"]

    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(_koord(nt), sep.inputs[0])
    a = _matematik(nt, 'MULTIPLY_ADD', _matematik(nt, 'SUBTRACT', sep.outputs[1], sep.outputs[0]),
                   oz("p_ax"), sep.outputs[0])                     # duvar boyunca konum (m)
    a0, a1, z0, z1 = oz("p_a0"), oz("p_a1"), oz("p_z0"), oz("p_z1")
    u = _matematik(nt, 'DIVIDE', _matematik(nt, 'SUBTRACT', a, a0), _matematik(nt, 'SUBTRACT', a1, a0))
    v = _matematik(nt, 'DIVIDE', _matematik(nt, 'SUBTRACT', sep.outputs[2], z0),
                   _matematik(nt, 'SUBTRACT', z1, z0))
    r = [_rastgele(nt, "p_id", k * 1.37) for k in range(6)]
    sol = _matematik(nt, 'MULTIPLY_ADD', _matematik(nt, 'POWER', r[0], 3.0), 0.44, 0.07)
    sag = _matematik(nt, 'MULTIPLY_ADD', _matematik(nt, 'POWER', r[1], 3.0), 0.44, 0.07)
    fon = _matematik(nt, 'MAXIMUM', _matematik(nt, 'LESS_THAN', u, sol),
                     _matematik(nt, 'GREATER_THAN', u, _matematik(nt, 'SUBTRACT', 1.0, sag)))
    stor = _matematik(nt, 'MULTIPLY', _matematik(nt, 'GREATER_THAN', r[2], 0.86),
                      _matematik(nt, 'GREATER_THAN', v,
                                 _matematik(nt, 'MULTIPLY_ADD', r[3], -0.5, 0.75)))
    opak = _matematik(nt, 'MAXIMUM', fon, stor)
    alfa = _matematik(nt, 'MAXIMUM', opak,
                      _matematik(nt, 'MULTIPLY', _matematik(nt, 'GREATER_THAN', r[4], 0.70), 0.50))
    kivrim = _matematik(nt, 'MULTIPLY_ADD',
                        _matematik(nt, 'SINE', _matematik(nt, 'MULTIPLY', a, 2 * math.pi / 0.14)),
                        0.14, 0.86)
    fon_renk = _olcekle(nt, _secim(nt, r[5], [renk("#D9CDBB"), renk("#EFE9DF"), renk("#9C9488"),
                                              renk("#7E6E5E"), renk("#C8C2B4"), renk("#5E6A63")]),
                        kivrim)
    tul = nt.nodes.new("ShaderNodeRGB")
    tul.outputs[0].default_value = (0.93, 0.91, 0.87, 1.0)
    c = _karistir(nt, opak, _olcekle(nt, tul.outputs[0], kivrim), fon_renk)
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    nt.links.new(c, df.inputs[0])
    tl = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(c, tl.inputs[0])
    kumas = nt.nodes.new("ShaderNodeMixShader")
    kumas.inputs[0].default_value = 0.35
    nt.links.new(df.outputs[0], kumas.inputs[1])
    nt.links.new(tl.outputs[0], kumas.inputs[2])
    sf = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alfa, mx.inputs[0])
    nt.links.new(sf.outputs[0], mx.inputs[1])
    nt.links.new(kumas.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
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
        "silme": mat_duz("Kat_Silmesi", P["silme"], 0.40, spec=0.45, var=0.05, olcek=2.0),
        "traverten": mat_traverten(P["traverten"]),
        "antrasit": mat_duz("Antrasit", P["antrasit"], 0.38, coat=0.15, var=0.05),
        "kaide": mat_duz("Bazalt_Kaide", P["kaide"], 0.6, var=0.12, olcek=3, bump=0.1),
        "bronz": mat_duz("Sampanya_Bronz", P["bronz"], 0.30, metal=1.0, var=0.04),
        "ahsap": mat_ahsap(P["ahsap"]),
        "cam": mat_cam_ince(P["cam"]),
        "perde": mat_perde(),
        "ic_siva": mat_duz("Ic_Siva", "#EAE5DC", 0.9, spec=0.3, var=0.02),
        "ic_duvar": mat_ic("Ic_Duvar", [renk("#EDE7DD"), renk("#E4DCCF"), renk("#F2EFE9"),
                                        renk("#D9D2C6"), renk("#C9B9A3")], 0.85, isik=0.30, ofset=1.1),
        "ic_tavan": mat_ic("Ic_Tavan", [renk("#F4F1EC")], 0.9, isik=1.4),
        "ic_zemin": mat_parke(),
        "doseme": mat_ic("Doseme_Kumas", [renk("#8C857B"), renk("#C9BBA6"), renk("#3E4A5C"),
                                          renk("#6F7B65"), renk("#A0644A"), renk("#D8D2C6"),
                                          renk("#55504A")], 0.95, ofset=2.2, spec=0.2),
        "hali": mat_ic("Hali", [renk("#CFC3AF"), renk("#8E9AA5"), renk("#B88C6E"), renk("#E2DDD3"),
                                renk("#6E6A66")], 0.98, ofset=5.5, spec=0.15),
        "tablo": mat_ic("Tablo", [renk("#2F5D7C"), renk("#C46A3C"), renk("#E9DFC9"), renk("#3B3B3B"),
                                  renk("#7E9C7A"), renk("#B7A06B")], 0.6, ofset=7.7),
        "nevresim": mat_duz("Nevresim", "#F3F0EA", 0.9, spec=0.2, var=0.03),
        "mob_ahsap": mat_duz("Mobilya_Ahsap", "#7B5B40", 0.45, var=0.08, olcek=4.0),
        "lake": mat_duz("Lake_Mutfak", "#ECE8E1", 0.22, coat=0.3, var=0.02),
        "koyu": mat_duz("Mobilya_Koyu", "#202124", 0.35, var=0.02),
        "lamba": mat_lamba(),
        "korkuluk": mat_seffaf("Cam_Korkuluk", P["korkuluk"]),
        "tas": tas,
        "minder": mat_duz("Minder", P["minder"], 0.9, spec=0.2, var=0.03),
        "yesil": mat_bitki("Bitki_Cit", P["yesil"], pus=False),
        "cati": mat_duz("Cati_Cakil", P["cati"], 0.92, spec=0.3, var=0.08, olcek=4.0, bump=0.3,
                        bump_olcek=70.0),
        "cim": mat_pbr("Cim", "cim", 2.6, P["cim"], ton=(0.88, 1.05, 0.80), koord="Position",
                       var=0.22, pus=False, rough=0.9, bump=0.15),
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
def _kontur(t, balkon=True, o=0.0, r=0.0, nis=True):
    """Blok taban konturu (saat yönü tersine): uçlarda salon bölgeleri, ortada yatak odası bandı,
    kuzey ve güney giriş nişleri. balkon=True: uçlardaki balkonlar dahil (r > 0 ise balkonların
    dış köşeleri yuvarlatılır); o: dışa ofset; nis=False: nişler dolu (geniş ofsetler için)."""
    X = t["xb"] if balkon else t["xs"]
    xr, yu, yo = t["xr"], t["yu"], t["yo"]
    yuv = balkon and r > 0
    nx, ny = (t["nx"], t["ny"]) if nis else (0.0, yo)
    sag = [(0.0, -ny, False), (nx, -ny, False), (nx, -yo, False), (xr, -yo, False),
           (xr, -yu, False), (X, -yu, yuv), (X, yu, yuv), (xr, yu, False), (xr, yo, False),
           (nx, yo, False), (nx, ny, False), (0.0, ny, False)]
    ham = []
    for p in sag + [(-x, y, k) for x, y, k in reversed(sag)]:
        if ham and abs(ham[-1][0] - p[0]) + abs(ham[-1][1] - p[1]) < 1e-6:
            ham[-1] = (p[0], p[1], ham[-1][2] or p[2])
        else:
            ham.append(p)
    if abs(ham[0][0] - ham[-1][0]) + abs(ham[0][1] - ham[-1][1]) < 1e-6:
        ham.pop()
    n = len(ham)
    pts = [p for i, p in enumerate(ham)
           if abs((p[0] - ham[i - 1][0]) * (ham[(i + 1) % n][1] - p[1]) -
                  (p[1] - ham[i - 1][1]) * (ham[(i + 1) % n][0] - p[0])) > 1e-9]
    out, n = [], len(pts)
    for i, (x, y, k) in enumerate(pts):
        n1 = _sol_normal((x, y), pts[i - 1])            # gelen kenarın dış normali
        n2 = _sol_normal(pts[(i + 1) % n], (x, y))      # giden kenarın dış normali
        if k:
            a0 = math.degrees(math.atan2(n1[1], n1[0]))
            a1 = math.degrees(math.atan2(n2[1], n2[0]))
            out += _yay(x - r * (n1[0] + n2[0]), y - r * (n1[1] + n2[1]), r + o, a0,
                        a1 + 360 if a1 < a0 else a1, 8)
        else:
            s = o / (1.0 + n1[0] * n2[0] + n1[1] * n2[1])
            out.append((x + s * (n1[0] + n2[0]), y + s * (n1[1] + n2[1])))
    return out


def _balkon_hatti(t, sx, sy, i=0.07):
    """Uç balkonunun açık kenarları boyunca korkuluk hattı: cephedeki dolu duvarın ucundan
    yuvarlatılmış köşeye, oradan iki daireyi ayıran bölme duvarına."""
    xb, yu = t["xb"], t["yu"]
    e = SILME - i
    pts = ([(t["bk"], yu + e)] + _yay(xb - R_KOSE, yu - R_KOSE, R_KOSE + e, 90, 0, 8) +
           [(xb + e, 0.12)])
    return [(sx * x, sy * y) for x, y in pts]


def _duzlem(eksen, w, a0, a1, z0, z1):
    """Duvar düzleminde dörtgen (eksen 'y': y = w düzlemi, a: x; 'x': x = w, a: y)."""
    if eksen == "y":
        return [(a0, w, z0), (a1, w, z0), (a1, w, z1), (a0, w, z1)]
    return [(w, a0, z0), (w, a1, z0), (w, a1, z1), (w, a0, z1)]


def _kutu_d(g, eksen, wa, wb, a0, a1, z0, z1, mat):
    """Duvara göre kutu: w (duvar normali boyunca) × a (duvar boyunca) × z."""
    wa, wb = sorted((wa, wb))
    if eksen == "y":
        g.kutu(a0, a1, wa, wb, z0, z1, mat)
    else:
        g.kutu(wa, wb, a0, a1, z0, z1, mat)


def _duvar_kutu(g, eksen, w0, n, a0, a1, z0, z1, dis, ic, ust=None, alt=None):
    """Dış yüzü w0'da, DUVAR_T kalınlığında duvar parçası: dış yüz ve söveler 'dis', iç yüz 'ic'."""
    wa, wb = sorted((w0, w0 - n * DUVAR_T))
    if eksen == "y":
        g.kutu6(a0, a1, wa, wb, z0, z1, {"v": dis, "-z": alt, "+z": ust, ("-y" if n > 0 else "+y"): ic})
    else:
        g.kutu6(wa, wb, a0, a1, z0, z1, {"v": dis, "-z": alt, "+z": ust, ("-x" if n > 0 else "+x"): ic})


def _duvarlar(g, M, t, aciklik, zf, zt):
    """Gövde konturunun her kenarında kat bandı boyunca açıklıklar dışında kalan duvar parçaları
    (dış yüz traverten, giriş nişlerinde antrasit; iç yüz sıva)."""
    nx, ny = t["nx"], t["ny"]
    pts = _kontur(t, False)
    for p, q in zip(pts, pts[1:] + pts[:1]):
        if abs(p[1] - q[1]) < 1e-6:
            eksen, w0, n = "y", p[1], (1 if q[0] < p[0] else -1)
            amin, amax = sorted((p[0], q[0]))
            nis = abs(abs(w0) - ny) < 1e-6 and amax <= nx + 1e-6
        else:
            eksen, w0, n = "x", p[0], (1 if q[1] > p[1] else -1)
            amin, amax = sorted((p[1], q[1]))
            nis = abs(abs(w0) - nx) < 1e-6
        dis = M["antrasit"] if nis else M["traverten"]
        bu = sorted((a for a in aciklik if a["eksen"] == eksen and abs(a["w0"] - w0) < 1e-6 and
                     a["n"] == n and amin - 1e-6 <= a["a0"] and a["a1"] <= amax + 1e-6),
                    key=lambda a: a["a0"])
        imlec = amin
        for a in bu:
            if a["a0"] > imlec + 1e-6:
                _duvar_kutu(g, eksen, w0, n, imlec, a["a0"], zf, zt, dis, M["ic_siva"])
            if a["z0"] > zf + 1e-6:
                _duvar_kutu(g, eksen, w0, n, a["a0"], a["a1"], zf, a["z0"], dis, M["ic_siva"], ust=dis)
            if a["z1"] < zt - 1e-6:
                _duvar_kutu(g, eksen, w0, n, a["a0"], a["a1"], a["z1"], zt, dis, M["ic_siva"], alt=dis)
            imlec = a["a1"]
        if amax > imlec + 1e-6:
            _duvar_kutu(g, eksen, w0, n, imlec, amax, zf, zt, dis, M["ic_siva"])


def _pencere(g, M, eksen, w0, n, a0, a1, z0, z1, dikme=0):
    """Söveye oturan sabit cam: söve içinde bronz kasa ve dikmeler."""
    g.dortgen(_duzlem(eksen, w0 - n * CAM_GERI, a0, a1, z0, z1), M["cam"])
    k0, k1 = w0 - n * 0.05, w0 - n * 0.15
    for p in ((a0, a0 + 0.06, z0, z1), (a1 - 0.06, a1, z0, z1),
              (a0, a1, z0, z0 + 0.06), (a0, a1, z1 - 0.06, z1)):
        _kutu_d(g, eksen, k0, k1, *p, M["bronz"])
    for k in range(1, dikme + 1):
        a = a0 + (a1 - a0) * k / (dikme + 1)
        _kutu_d(g, eksen, w0 - n * 0.06, w0 - n * 0.14, a - 0.025, a + 0.025, z0, z1, M["bronz"])


def _surme(g, M, eksen, w0, n, a0, a1, z0, z1, acik=0.0):
    """İki kanatlı sürme kapı: dış raydaki kanat sabit, iç raydaki kanat 'acik' oranında aralık."""
    for p in ((a0, a0 + 0.05, z0, z1), (a1 - 0.05, a1, z0, z1),
              (a0, a1, z0, z0 + 0.05), (a0, a1, z1 - 0.05, z1)):
        _kutu_d(g, eksen, w0 - n * 0.04, w0 - n * 0.17, *p, M["bronz"])
    pw = (a1 - a0) / 2 + 0.03
    s = acik * (pw - 0.12)
    for (b0, b1), wr in (((a0, a0 + pw), w0 - n * 0.08), ((a1 - pw - s, a1 - s), w0 - n * 0.13)):
        g.dortgen(_duzlem(eksen, wr, b0, b1, z0 + 0.05, z1 - 0.05), M["cam"])
        for p in ((b0, b0 + 0.06, z0 + 0.05, z1 - 0.05), (b1 - 0.06, b1, z0 + 0.05, z1 - 0.05),
                  (b0, b1, z0 + 0.05, z0 + 0.11), (b0, b1, z1 - 0.11, z1 - 0.05)):
            _kutu_d(g, eksen, wr - 0.02, wr + 0.02, *p, M["bronz"])


def _giris(g, M, eksen, w0, n, a0, a1, z0, z1):
    """Bina girişi: iki kanatlı cam kapı, üstte vasistas, yanlarda sabit cam, bronz kollar."""
    _pencere(g, M, eksen, w0, n, a0, a1, z0, z1)
    wa, wb = w0 - n * 0.05, w0 - n * 0.15
    _kutu_d(g, eksen, wa, wb, a0, a1, z0 + 2.40, z0 + 2.46, M["bronz"])
    for a in (-0.75, 0.0, 0.75):
        if a0 + 0.1 < a < a1 - 0.1:
            _kutu_d(g, eksen, wa, wb, a - 0.03, a + 0.03, z0, z0 + 2.40, M["bronz"])
    for a in (-0.12, 0.12):
        _kutu_d(g, eksen, w0 - n * 0.02, w0 - n * 0.06, a - 0.015, a + 0.015, z0 + 0.9, z0 + 1.5,
                M["bronz"])


def _fransiz(g, M, eksen, w0, n, a0, a1, z):
    """Yerden tavana camın önünde, döşeme alnı üstünde çerçevesiz cam korkuluk."""
    w = w0 + n * 0.14
    h = [(a0, w), (a1, w)] if eksen == "y" else [(w, a0), (w, a1)]
    g.serit(h, z, z + 1.05, 0.024, M["korkuluk"])
    g.serit(h, z + 1.05, z + 1.085, 0.05, M["bronz"])


def _perde(g, M, a, rid, k, zf, zt):
    """Duvarın iç yüzünden 10 cm geride, iki yanda 20 cm taşan perde (açıklığı shader belirler)."""
    a0, a1, z0, z1 = a["a0"] - 0.20, a["a1"] + 0.20, zf + 0.02, zt - 0.04
    g.ozellik(oda=rid, p_ax=0.0 if a["eksen"] == "y" else 1.0, p_a0=a0, p_a1=a1, p_z0=z0, p_z1=z1,
              p_id=rid * 10.0 + k)
    g.dortgen(_duzlem(a["eksen"], a["w0"] - a["n"] * (DUVAR_T + 0.10), a0, a1, z0, z1), M["perde"])
    g.ozellik(oda=rid)


def _yerel(r, on, ayna):
    """Oda yerel koordinatı: s pencere duvarı boyunca (0..W), t pencereden içeri (0..D)."""
    x0, x1, y0, y1 = r
    W, D = (x1 - x0, y1 - y0) if on in ("-y", "+y") else (y1 - y0, x1 - x0)

    def donus(s0, s1, t0, t1):
        if ayna:
            s0, s1 = W - s1, W - s0
        if on == "-y":
            return x0 + s0, x0 + s1, y0 + t0, y0 + t1
        if on == "+y":
            return x0 + s0, x0 + s1, y1 - t1, y1 - t0
        if on == "-x":
            return x0 + t0, x0 + t1, y0 + s0, y0 + s1
        return x1 - t1, x1 - t0, y0 + s0, y0 + s1
    return W, D, donus


def _oda_kabugu(g, M, r, dis, zf, zt):
    """Parke, tavan ve iç bölmeler. Dış duvar taraflarında (dis) bölme yok; zemin ve tavan
    cam hattına kadar uzar."""
    x0, x1, y0, y1 = r
    e = DUVAR_T - CAM_GERI
    X0, X1 = x0 - e * ("-x" in dis), x1 + e * ("+x" in dis)
    Y0, Y1 = y0 - e * ("-y" in dis), y1 + e * ("+y" in dis)
    za, zb = zf + 0.005, zt - 0.005
    g.dortgen([(X0, Y0, za), (X1, Y0, za), (X1, Y1, za), (X0, Y1, za)], M["ic_zemin"])
    g.dortgen([(X0, Y0, zb), (X0, Y1, zb), (X1, Y1, zb), (X1, Y0, zb)], M["ic_tavan"])
    for k, (a, b) in (("-x", ((x0, y1), (x0, y0))), ("+x", ((x1, y0), (x1, y1))),
                      ("-y", ((x0, y0), (x1, y0))), ("+y", ((x1, y1), (x0, y1)))):
        if k not in dis:
            g.dortgen([(a[0], a[1], zf), (b[0], b[1], zf), (b[0], b[1], zt), (a[0], a[1], zt)],
                      M["ic_duvar"])


def _mobilya(g, M, oda, zf, zt):
    """Kat planındaki odalara göre mobilya (s pencere duvarı boyunca, t pencereden içeri).
    salon: arka duvarda mutfak nişi, yemek masası, kanepe; s = W balkon kapısı tarafı.
    oda9: çift kişilik yatak + dolap; oda6: tek kişilik yatak + pencere önünde çalışma masası;
    hol: sarkıt, tablo, bitki."""
    W, D, T = _yerel(oda["r"], oda["on"], oda["ayna"])

    def kutu(s0, s1, t0, t1, z0, z1, mat):
        xa, xb, ya, yb = T(s0, s1, t0, t1)
        g.kutu(xa, xb, ya, yb, zf + z0, zf + z1, mat)

    def nokta(s, t):
        xa, _, ya, _ = T(s, s, t, t)
        return xa, ya

    def saksi(s, t, r=0.22, h=0.45, tac=0.38):
        x, y = nokta(s, t)
        g.silindir((x, y, zf), (x, y, zf + h), r, M["antrasit"], 10)
        g.kure((x, y, zf + h + tac * 1.2), (tac, tac, tac * 1.4), M["yesil"], 10, 6, 0.3, x * 0.7 + y)

    def sarkit(s, t, r=0.15, boy=0.62):
        x, y = nokta(s, t)
        g.silindir((x, y, zt - 0.01), (x, y, zt - boy), 0.008, M["koyu"], 4)
        g.kure((x, y, zt - boy - 0.1), (r, r, r * 0.8), M["lamba"], 8, 5)

    def yatak(s0, s1, t0, t1, bas):
        """Yatak: baza, nevresim, ayak ucunda örtü, başlık tarafında yastıklar ve başlık.
        bas: başlığın olduğu kenar ('s0', 's1', 't1')."""
        kutu(s0, s1, t0, t1, 0.0, 0.32, M["doseme"])
        kutu(s0 + 0.02, s1 - 0.02, t0 + 0.02, t1 - 0.02, 0.32, 0.55, M["nevresim"])
        ust = {"s0": (s1 - 0.62, s1 + 0.01, t0 - 0.01, t1 + 0.01),
               "s1": (s0 - 0.01, s0 + 0.62, t0 - 0.01, t1 + 0.01),
               "t1": (s0 - 0.01, s1 + 0.01, t0 - 0.01, t0 + 0.62)}[bas]
        kutu(*ust, 0.50, 0.58, M["doseme"])
        if bas == "t1":
            n = 2 if s1 - s0 > 1.2 else 1
            for k in range(n):
                c = s0 + (s1 - s0) * (k + 0.5) / n
                kutu(c - 0.3, c + 0.3, t1 - 0.5, t1 - 0.12, 0.55, 0.70, M["nevresim"])
            kutu(s0 - 0.05, s1 + 0.05, t1, t1 + 0.07, 0.0, 1.10, M["doseme"])
        else:
            n = 2 if t1 - t0 > 1.2 else 1
            sa, sb = (s0 + 0.12, s0 + 0.5) if bas == "s0" else (s1 - 0.5, s1 - 0.12)
            for k in range(n):
                c = t0 + (t1 - t0) * (k + 0.5) / n
                kutu(sa, sb, c - 0.3, c + 0.3, 0.55, 0.70, M["nevresim"])
            ba, bb = (s0 - 0.07, s0) if bas == "s0" else (s1, s1 + 0.07)
            kutu(ba, bb, t0 - 0.05, t1 + 0.05, 0.0, 1.10, M["doseme"])

    tur = oda["tur"]
    if tur == "salon":
        # arka (ortak) duvarda mutfak nişi: alt dolap, tezgâh, üst dolap
        kutu(0.10, W - 0.10, D - 0.62, D, 0.0, 0.88, M["lake"])
        kutu(0.10, W - 0.10, D - 0.64, D, 0.88, 0.92, M["koyu"])
        kutu(0.10, W - 0.10, D - 0.36, D, 1.50, 2.25, M["lake"])
        # yemek masası, dört sandalye, üstünde iki sarkıt
        sm, tm = W * 0.5, D - 1.55
        kutu(sm - 0.75, sm + 0.75, tm - 0.42, tm + 0.42, 0.72, 0.76, M["mob_ahsap"])
        kutu(sm - 0.05, sm + 0.05, tm - 0.30, tm + 0.30, 0.0, 0.72, M["koyu"])
        for ds in (-0.4, 0.4):
            for dt in (-1, 1):
                ct = tm + dt * 0.66
                kutu(sm + ds - 0.2, sm + ds + 0.2, ct - 0.2, ct + 0.2, 0.42, 0.47, M["doseme"])
                b0, b1 = sorted((ct + dt * 0.16, ct + dt * 0.21))
                kutu(sm + ds - 0.2, sm + ds + 0.2, b0, b1, 0.47, 0.88, M["doseme"])
            sarkit(sm + ds, tm)
        # iç yan duvara dayalı kanepe (balkon kapısına, manzaraya bakar), sehpa, halı, tablo
        t0, t1 = 0.45, min(2.45, tm - 1.05)
        kutu(0.05, 0.95, t0, t1, 0.0, 0.42, M["doseme"])
        kutu(0.05, 0.30, t0, t1, 0.42, 0.85, M["doseme"])
        for tt in (t0, t1 - 0.2):
            kutu(0.05, 0.95, tt, tt + 0.2, 0.42, 0.62, M["doseme"])
        kutu(0.25, min(W - 0.3, 2.6), t0 - 0.1, t1 + 0.1, 0.0, 0.012, M["hali"])
        kutu(1.25, 1.90, t0 + 0.40, t1 - 0.40, 0.0, 0.38, M["mob_ahsap"])
        kutu(0.0, 0.03, t0 + 0.30, t1 - 0.30, 1.25, 1.90, M["tablo"])
        x, y = nokta(0.35, t1 + 0.35)
        g.silindir((x, y, zf), (x, y, zf + 1.45), 0.015, M["koyu"], 4)
        g.silindir((x, y, zf + 1.45), (x, y, zf + 1.75), 0.2, M["lamba"], 10)
        saksi(W - 0.40, 0.40)
    elif tur == "oda9":                       # başlık balkon/salon tarafındaki yan duvarda
        bt0 = max(0.40, (D - 1.6) / 2)
        bt1 = min(D - 0.08, bt0 + 1.6)
        yatak(W - 2.12, W - 0.07, bt0, bt1, "s1")
        for c0, c1 in ((bt0 - 0.38, bt0 - 0.02), (bt1 + 0.02, bt1 + 0.38)):
            if c0 >= 0.02 and c1 <= D - 0.02:
                kutu(W - 0.45, W - 0.05, c0, c1, 0.0, 0.48, M["mob_ahsap"])
                x, y = nokta(W - 0.25, (c0 + c1) / 2)
                g.silindir((x, y, zf + 0.48), (x, y, zf + 0.76), 0.11, M["lamba"], 8)
        if W - 2.12 > 0.9:                    # karşı duvarda gardırop
            kutu(0.02, 0.62, max(0.35, D - 2.0), D - 0.02, 0.0, 2.35, M["lake"])
        kutu(W - 0.03, W, (bt0 + bt1) / 2 - 0.5, (bt0 + bt1) / 2 + 0.5, 1.30, 1.90, M["tablo"])
        kutu(0.8, min(W - 0.3, 2.6), bt0 - 0.25, bt1 - 0.2, 0.0, 0.012, M["hali"])
        sarkit(W / 2, D / 2, 0.22, 0.45)
    elif tur == "oda6":                       # tek kişilik yatak + pencere önünde çalışma masası
        if W >= 2.15:
            yatak(0.05, 2.05, D - 0.97, D - 0.05, "s0")
            m0, m1 = W - 1.15, W - 0.10
        else:
            yatak(0.05, 0.97, D - 2.07, D - 0.05, "t1")
            m0, m1 = min(1.02, W - 0.9), W - 0.06
        kutu(m0, m1, 0.06, 0.62, 0.72, 0.76, M["mob_ahsap"])
        for c in (m0 + 0.05, m1 - 0.05):
            kutu(c - 0.025, c + 0.025, 0.08, 0.60, 0.0, 0.72, M["koyu"])
        sm = (m0 + m1) / 2
        kutu(sm - 0.22, sm + 0.22, 0.70, 1.12, 0.42, 0.47, M["doseme"])
        kutu(sm - 0.22, sm + 0.22, 1.07, 1.12, 0.47, 0.90, M["doseme"])
        x, y = nokta(m1 - 0.2, 0.3)
        g.silindir((x, y, zf + 0.76), (x, y, zf + 1.15), 0.09, M["lamba"], 8)
        kutu(0.0, 0.03, 0.6, min(D - 1.1, 1.6), 1.25, 1.75, M["tablo"])
        sarkit(W / 2, D / 2, 0.2, 0.45)
    else:                                     # kat holü / bina giriş lobisi
        x, y = nokta(W / 2, D / 2)
        g.silindir((x, y, zt - 0.01), (x, y, zt - 0.5), 0.01, M["koyu"], 4)
        g.kure((x, y, zt - 0.7), (0.28, 0.28, 0.22), M["lamba"], 10, 6)
        kutu(W / 2 - 0.6, W / 2 + 0.6, D - 0.03, D, 1.2, 2.0, M["tablo"])
        saksi(0.35, D - 0.4, 0.25, 0.55, 0.45)


def _balkon_mobilya(g, M, t, z, sx, sy, kat):
    """Uç balkonu: tek katlarda iki şezlong, çift katlarda yemek masası; cephedeki dolu duvarın
    dibinde saksıda zeytin."""
    xs, xb, yu = t["xs"], t["xb"], t["yu"]
    xm = sx * (xs + xb) / 2
    if kat % 2:
        ya, yb = 0.62, 0.62 + 1.84               # başlık bölme duvarı tarafında, ayak ucu cepheye
        for k in (-1, 1):
            x = xm + k * 0.50
            y0, y1 = sorted((sy * ya, sy * yb))
            g.kutu(x - 0.32, x + 0.32, y0, y1, z + 0.12, z + 0.30, M["ahsap"])
            y0, y1 = sorted((sy * (ya + 0.55), sy * yb))
            g.kutu(x - 0.30, x + 0.30, y0, y1, z + 0.30, z + 0.38, M["minder"])
            g.kutu_m((x, sy * (ya + 0.28), z + 0.55), (0.30, 0.26, 0.05),
                     Matrix.Rotation(math.radians(-55 * sy), 3, 'X'), M["minder"])
    else:
        ym = sy * yu * 0.55
        g.kutu(xm - 0.42, xm + 0.42, ym - 0.60, ym + 0.60, z + 0.72, z + 0.76, M["ahsap"])
        g.kutu(xm - 0.05, xm + 0.05, ym - 0.05, ym + 0.05, z, z + 0.72, M["bronz"])
        for dy in (-0.32, 0.32):
            for k in (-1, 1):
                cx = xm + k * 0.72
                g.kutu(cx - 0.21, cx + 0.21, ym + dy - 0.21, ym + dy + 0.21, z + 0.42, z + 0.47,
                       M["minder"])
                bx0, bx1 = sorted((cx + k * 0.17, cx + k * 0.22))
                g.kutu(bx0, bx1, ym + dy - 0.21, ym + dy + 0.21, z + 0.47, z + 0.85, M["ahsap"])
    px, py = sx * (xs + 0.45), sy * (yu - 0.55)
    g.silindir((px, py, z), (px, py, z + 0.55), 0.28, M["antrasit"], 10)
    g.silindir((px, py, z + 0.55), (px, py, z + 1.15), 0.04, M["ahsap"], 6)
    g.kure((px, py, z + 1.45), (0.50, 0.48, 0.40), M["zeytin"], 10, 6, 0.25, kat * 1.7 + sx + sy * 0.4)


def blok_tipi(M, coll, ad, t):
    """T_P-4 kat planındaki blok: kuzey ve güney yarıda ikişer 2+1, uçlarda balkonlu salonlar,
    cephede yatak odaları, ortada asansör + merdiven çekirdeği, kuzeyde bina girişi nişi.
    Salon cephesinde Fransız cam, balkon tarafında sürgülü cam; yatak odalarında 1,50 x 1,50 m
    pencere. Camların arkasında döşenmiş odalar; perde ve ışıklar blok ve oda başına değişir."""
    g = Govde()
    xb, xs, xr, yu, yo, nx, ny = (t[k] for k in ("xb", "xs", "xr", "yu", "yo", "nx", "ny"))
    Zc = Z0 + KAT * KAT_H                    # çatı döşemesi üstü
    Zt = Zc - DOSEME_T                       # gövde üstü
    zk = Z0 + KAT_H                          # 1. kat döşemesi
    rnd = random.Random(TOHUM + int(xb * 100))

    # zemin: bazalt kaide (zemin kat balkon terasları dahil), cephe önünde alçak çit
    g.prizma(_kontur(t, True, 0.30, R_KOSE), 0.0, Z0, M["kaide"], ust=M["tas"], alt=False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for (a0, a1), y in (((nx + 1.4, xr - 0.1), yo), ((xr + 0.1, xb - 1.2), yu)):
                if a1 - a0 > 0.5:
                    x0, x1 = sorted((sx * a0, sx * a1))
                    y0, y1 = sorted((sy * (y + 0.32), sy * (y + 0.85)))
                    g.kutu(x0, x1, y0, y1, 0.0, 0.85, M["yesil"])

    # ara döşemeler: kat silmeleri (koyu alın bantları), tik tavan, taş balkon zemini
    for i in range(1, KAT):
        z = Z0 + i * KAT_H
        g.prizma(_kontur(t, True, SILME, R_KOSE), z - DOSEME_T, z, M["silme"], ust=M["tas"],
                 alt=M["ahsap"])

    # çatı: üst kat balkonlarını da örten saçak (yan yüzü kat silmesi rengi), çakıl,
    # asansör + merdiven kulesi
    g.prizma(_kontur(t, True, SILME + 0.15, R_KOSE), Zt, Zc + 0.25, M["silme"], ust=M["cati"],
             alt=M["ahsap"])
    g.prizma(_kontur(t, False, -0.40), Zc + 0.25, Zc + 0.29, M["cati"], alt=False)
    g.kutu(-3.75, 3.75, -1.85, 1.85, Zc + 0.25, Zc + 2.9, M["traverten"], alt=False)
    g.kutu(-3.9, 3.9, -2.0, 2.0, Zc + 2.9, Zc + 3.1, M["silme"], alt=M["ahsap"])
    g.kutu(0.8, 1.9, 1.83, 1.88, Zc + 0.29, Zc + 2.45, M["antrasit"])

    # balkonlar: çerçevesiz cam korkuluk + bronz küpeşte, cephede dolu traverten duvar, iki
    # daireyi ayıran bölme duvarı; mobilya (zemin kat terası dahil)
    for i in range(KAT):
        z = Z0 + i * KAT_H
        z1 = z + KAT_H - DOSEME_T
        for sx in (-1, 1):
            x0, x1 = sorted((sx * xs, sx * (xb - 0.02)))
            g.kutu(x0, x1, -0.09, 0.09, z, z1, M["traverten"])
            for sy in (-1, 1):
                h = _balkon_hatti(t, sx, sy)
                g.serit(h, z, z + 1.05, 0.024, M["korkuluk"])
                g.serit(h, z + 1.05, z + 1.085, 0.05, M["bronz"])
                x0, x1 = sorted((sx * xs, sx * t["bk"]))
                y0, y1 = sorted((sy * (yu - 0.22), sy * yu))
                g.kutu(x0, x1, y0, y1, z, z1, M["traverten"])
                _balkon_mobilya(g, M, t, z, sx, sy, i)

    # katlar: açıklıklı duvarlar, camlar, sürme kapılar, arkalarında odalar
    for i in range(KAT):
        zf = Z0 + i * KAT_H
        zt = zf + KAT_H - DOSEME_T
        ac, odalar = [], []

        def oda(r, dis, on, tur, ayna=False):
            o = dict(id=1.0 + i * 20 + len(odalar), r=r, dis=dis, on=on, tur=tur, ayna=ayna, pen=[])
            odalar.append(o)
            return o

        def aciklik(o, **kw):
            ac.append(kw)
            o["pen"].append(kw)

        for sy in (-1, 1):
            on = "+y" if sy > 0 else "-y"
            for sx in (-1, 1):
                # salon + mutfak: cephede Fransız cam (yerden tavana, üst katlarda cam korkuluk),
                # balkon tarafında sürgülü cam kapı
                x0, x1 = sorted((sx * (xr + 0.05), sx * (xs - DUVAR_T)))
                y0, y1 = sorted((sy * 0.12, sy * (yu - DUVAR_T)))
                s = oda((x0, x1, y0, y1), {on, "+x" if sx > 0 else "-x"}, on, "salon", sx < 0)
                a0, a1 = sorted((sx * (xr + 0.35), sx * (xs - 0.45)))
                aciklik(s, eksen="y", w0=sy * yu, n=sy, a0=a0, a1=a1, z0=zf, z1=zt, tur="pencere",
                        dikme=2, fransiz=i > 0)
                b0, b1 = sorted((sy * 0.95, sy * (yu - 0.45)))
                aciklik(s, eksen="x", w0=sx * xs, n=sx, a0=b0, a1=b1, z0=zf, z1=zt, tur="surme",
                        acik=rnd.choice((0.0, 0.0, 0.0, 0.45, 0.85)))
                # yatak odaları: oda cephesinde ortalanmış parapetli normal pencere
                pw, ph, pp = ODA_PENCERE
                for tur, (r0, r1) in (("oda9", t["oda9"]), ("oda6", t["oda6"])):
                    x0, x1 = sorted((sx * r0, sx * r1))
                    y0, y1 = sorted((sy * t["oy"], sy * (yo - DUVAR_T)))
                    o = oda((x0, x1, y0, y1), {on}, on, tur, sx < 0)
                    xm = sx * (r0 + r1) / 2
                    aciklik(o, eksen="y", w0=sy * yo, n=sy, a0=xm - pw / 2, a1=xm + pw / 2,
                            z0=zf + pp, z1=zf + pp + ph, tur="pencere", dikme=1)
            # niş dibinde kat holü: zemin katta kuzeyde bina girişi, diğerlerinde pencere
            y0, y1 = sorted((sy * 1.60, sy * (ny - DUVAR_T)))
            h = oda((-2.1, 2.1, y0, y1), {on}, on, "hol")
            aciklik(h, eksen="y", w0=sy * ny, n=sy, a0=-nx + 0.15, a1=nx - 0.15, z0=zf, z1=zt,
                    tur="giris" if (i == 0 and sy > 0) else "pencere", dikme=1)

        _duvarlar(g, M, t, ac, zf, zt)
        for a in ac:
            args = (g, M, a["eksen"], a["w0"], a["n"], a["a0"], a["a1"], a["z0"], a["z1"])
            if a["tur"] == "surme":
                _surme(*args, a["acik"])
            elif a["tur"] == "giris":
                _giris(*args)
            else:
                _pencere(*args, a["dikme"])
            if a.get("fransiz"):
                _fransiz(g, M, a["eksen"], a["w0"], a["n"], a["a0"], a["a1"], zf)
        for o in odalar:
            g.ozellik(oda=o["id"])
            _oda_kabugu(g, M, o["r"], o["dis"], zf, zt)
            _mobilya(g, M, o, zf, zt)
            if o["tur"] != "hol":
                for k, a in enumerate(o["pen"]):
                    _perde(g, M, a, o["id"], k, zf, zt)
            g.ozellik()

    # bina girişi (kuzey nişi): sahanlık, basamaklar, tik altlı saçak
    g.kutu(-nx, nx, ny, yo + 0.3, 0.0, Z0 - 0.005, M["kaide"], ust=M["tas"])
    for k in range(3):
        y0 = yo + 0.3 + 0.35 * k
        g.kutu(-nx - 0.4, nx + 0.4, y0, y0 + 0.35, 0.0, Z0 - 0.15 * (k + 1), M["kaide"], ust=M["tas"])
    g.kutu(-nx - 0.8, nx + 0.8, ny + 0.5, yo + 1.5, zk - DOSEME_T + 0.01, zk - 0.01, M["silme"],
           alt=M["ahsap"])
    return g.obje(ad, coll)


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
    """Vaziyet planındaki dizi: her parselde tek sıra, A bloğu kuzeyde (denizden uzak).
    İlk ve son blok plandaki yerinde, aradakiler eşit aralıkla."""
    bloklar = []
    for pid, d in DIZI.items():
        (u0, v0), (u1, v1), n = d["kuzey"], d["guney"], d["adet"]
        for k in range(n):
            f = k / (n - 1) if n > 1 else 0.0
            bloklar.append(dict(ad=f"{pid}-{chr(65 + k)}", parsel=pid, tip=d["tip"],
                                u=u0 + (u1 - u0) * f, v=v0 + (v1 - v0) * f))
    return bloklar


def rapor(bloklar):
    arsa = {"7104": 5648.0, "7105": 4510.0}
    top = [0, 0, 0.0]
    print("\n================ YALOVA ARMUTLU – 7104 / 7105 ================")
    for pid in DIZI:
        bl = sorted((b for b in bloklar if b["parsel"] == pid), key=lambda b: -b["v"])
        if not bl:
            continue
        t = BLOK_TIPLERI[bl[0]["tip"]]
        B, D2 = t["xb"], max(t["yu"], t["yo"])
        taban = abs(_alan(_kontur(t, True)))
        brut = t["brut"] * KAT * len(bl)
        aralik = min((a["v"] - b["v"] - 2 * D2 for a, b in zip(bl, bl[1:])), default=0.0)
        daire = len(bl) * KAT * 4
        top[0] += len(bl); top[1] += daire; top[2] += brut
        print(f"{pid}: {len(bl)} blok ({bl[0]['tip']}, balkonlarla {2 * B:.1f} x {2 * D2:.1f} m) | "
              f"{daire} daire | blok tabanı {taban:.0f} m² | brüt {brut:,.0f} m²")
        print(f"      TAKS≈{taban * len(bl) / arsa[pid]:.2f}  KAKS≈{brut / arsa[pid]:.2f}  |  "
              f"bloklar arası net mesafe: {aralik:.1f} m")
    print(f"TOPLAM: {top[0]} blok | {top[1]} daire | brüt {top[2]:,.0f} m² | "
          f"bina yüksekliği {Z0 + KAT * KAT_H:.2f} m (+ çatı kulesi)")
    print("==============================================================\n")


# ============================== PEYZAJ ==============================
def _kenar_parcalari(poly, iceri, kapilar=()):
    """Parsel kenarlarını içe kaydırıp çizgi parçası olarak döndürür.
    kapilar: (kenar, u, genişlik) -> 'kuzey' / 'guney' kenarda giriş boşluğu."""
    n = len(poly)
    toplam = [poly[i][1] + poly[(i + 1) % n][1] for i in range(n)]
    secim = {"kuzey": toplam.index(max(toplam)), "guney": toplam.index(min(toplam))}
    parcalar = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        nx, ny = _sol_normal(a, b)
        a2, b2 = (a[0] + nx * iceri, a[1] + ny * iceri), (b[0] + nx * iceri, b[1] + ny * iceri)
        bosluk = [(u, w) for kenar, u, w in kapilar if secim[kenar] == i]
        if bosluk:
            u, w = bosluk[0]
            dx, dy = b2[0] - a2[0], b2[1] - a2[1]
            t0, t1 = sorted(((u - w / 2 - a2[0]) / dx, (u + w / 2 - a2[0]) / dx))
            if 0 < t0 < t1 < 1:
                parcalar.append([a2, (a2[0] + dx * t0, a2[1] + dy * t0)])
                parcalar.append([(a2[0] + dx * t1, a2[1] + dy * t1), b2])
                continue
        parcalar.append([a2, b2])
    return parcalar


def peyzaj(M, coll, bloklar, agac, agac_coll):
    """Havuzsuz site peyzajı: çim, bahçe duvarı + çit, blok çevresi taş döşeme, blok dizisine
    paralel yürüyüş yolları, bloklar arası geçitler; servi / zeytin / palmiye."""
    g = Govde()
    rnd = random.Random(TOHUM + 5)

    def agac_koy(tip, u, v, olcek=1.0):
        ornekle(tip.lower(), agac[tip], agac_coll, (u, v, 0.04), rnd.uniform(0, 6.28),
                olcek * rnd.uniform(0.9, 1.1))

    for pid, poly in (("7104", P7104), ("7105", P7105)):
        bl = sorted((b for b in bloklar if b["parsel"] == pid), key=lambda b: -b["v"])
        if not bl:
            continue
        t = BLOK_TIPLERI[bl[0]["tip"]]
        B, D2 = t["xb"], max(t["yu"], t["yo"])
        b0, b1 = bl[0], bl[-1]
        egim = (b1["u"] - b0["u"]) / (b1["v"] - b0["v"]) if len(bl) > 1 else 0.0

        def u_hat(v):                                   # blok dizisinin ekseni
            return b0["u"] + (v - b0["v"]) * egim

        u_m = u_hat((b0["v"] + b1["v"]) / 2)
        kapilar = (("kuzey", u_m, 6.0), ("guney", u_m, 4.0))
        g.prizma(poly, 0.0, 0.04, M["cim"], alt=False)
        for p in _kenar_parcalari(poly, 0.15, kapilar):
            g.serit(p, 0.0, 0.55, 0.25, M["beyaz"])
        for p in _kenar_parcalari(poly, 0.95, kapilar):
            g.serit(p, 0.0, 1.25, 0.8, M["yesil"])
        vk, vg = _kenar_v(poly, u_m, 1), _kenar_v(poly, u_m, -1)
        vt, va = vk - 1.6, vg + 1.6                      # yürüyüş yollarının uçları
        # blok dizisine paralel iki yürüyüş yolu + kuzey / güney bağlantıları + kapı aksları
        for sx in (-1, 1):
            w = sx * (B + 1.05)
            g.prizma([(u_hat(va) + w - 0.75, va), (u_hat(va) + w + 0.75, va),
                      (u_hat(vt) + w + 0.75, vt), (u_hat(vt) + w - 0.75, vt)], 0.0, 0.05, M["tas"],
                     alt=False)
        for vv, yon in ((vt, -1), (va, 1)):
            ua, ub = u_hat(vv) - B - 1.8, u_hat(vv) + B + 1.8
            g.kutu(ua, ub, *sorted((vv, vv + yon * 1.5)), 0.0, 0.05, M["tas"], alt=False)
        g.kutu(u_m - 1.5, u_m + 1.5, vt, vk - 0.1, 0.0, 0.05, M["tas"], alt=False)
        g.kutu(u_m - 1.5, u_m + 1.5, b0["v"] + D2 + 1.0, vt, 0.0, 0.05, M["tas"], alt=False)
        g.kutu(u_m - 1.2, u_m + 1.2, vg + 0.1, va, 0.0, 0.05, M["tas"], alt=False)
        g.kutu(u_m - 1.2, u_m + 1.2, va, b1["v"] - D2 - 1.0, 0.0, 0.05, M["tas"], alt=False)
        # blok çevresi taş döşeme
        for b in bl:
            g.prizma([(b["u"] + x, b["v"] + y) for x, y in _kontur(t, True, 1.3, R_KOSE, nis=False)],
                     0.0, 0.055, M["tas"], alt=False)
        # bloklar arası: dar geçit tümüyle taş, genişte çim şerit + iki zeytin
        konumlar = []
        for a, b in zip(bl, bl[1:]):
            vm, bos = (a["v"] + b["v"]) / 2, a["v"] - b["v"] - 2 * D2
            if bos < 4.5:
                g.kutu(u_hat(vm) - B - 1.8, u_hat(vm) + B + 1.8, vm - bos / 2, vm + bos / 2,
                       0.0, 0.052, M["tas"], alt=False)
            else:
                for du in (-6.0, 6.0):
                    agac_koy("AGAC_ZEYTIN", u_hat(vm) + du, vm, 0.75)
            konumlar.append(vm)
        # bina girişinin iki yanında küçük zeytin (balkon uçlarının önü açık kalır)
        for b in bl:
            for sx in (-1, 1):
                agac_koy("AGAC_ZEYTIN", b["u"] + sx * 2.6, b["v"] + D2 + 2.3, 0.6)
        # yan bahçe şeridi (yol ile çit arası) yer varsa servi
        for v in konumlar:
            for sx in (-1, 1):
                yol = u_hat(v) + sx * (B + 1.8)
                cit = _kenar_u(poly, v, sx) - sx * 1.35
                bos = sx * (cit - yol)
                if bos >= 1.5:
                    agac_koy("AGAC_SERVI", (yol + cit) / 2, v, min(1.0, bos / 2.2) * 0.9)
        # kuzey bahçe: zeytin; güney (deniz) bahçesi: palmiye
        for du in (-9.0, 9.0):
            agac_koy("AGAC_ZEYTIN", u_m + du, (vt + b0["v"] + D2 + 1.3) / 2, 0.85)
        vs = (va + b1["v"] - D2 - 1.3) / 2
        for du in (-11.5, -5.0, 5.0, 11.5):
            agac_koy("AGAC_PALMIYE", u_m + du, vs, 0.9)
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
                if any(math.hypot(cx - k[0], cy - k[1]) < 62 for k in cam_xy):
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
    # (düzenlemek için: Outliner > Blender File > Collections > TIP_BLOK_A264 / TIP_BLOK_B264)
    c_tip = {ad: bpy.data.collections.new("TIP_BLOK_" + ad) for ad in BLOK_TIPLERI}
    c_agac_tip = bpy.data.collections.new("TIP_AGAC")
    c_arac_tip = bpy.data.collections.new("TIP_ARAC")
    bloklar = yerlesim()
    c_proje = koleksiyon(f"PROJE_{len(bloklar)}_BLOK")
    c_peyzaj = koleksiyon("PEYZAJ")
    c_cevre = koleksiyon("CEVRE_DENIZ")
    c_kam = koleksiyon("KAMERA_ISIK")

    for ad, c in c_tip.items():
        blok_tipi(M, c, "BLOK_TIPI_" + ad, BLOK_TIPLERI[ad])
    agac = agac_tipleri(M, c_agac_tip)
    araclar = araba_tipleri(M, c_arac_tip)
    c_parsel = {pid: koleksiyon("PARSEL_" + pid, c_proje) for pid in DIZI}
    for b in bloklar:
        ornekle("BLOK_" + b["ad"], c_tip[b["tip"]], c_parsel[b["parsel"]], (b["u"], b["v"], 0.0))

    # Kamera 1: denizden, güneydoğudan kuşbakışı – tüm proje
    cam1 = kamera("CAM_GENEL", (138.0, -221.0, 70.0), (22.4, -46.0, 0.0), 35.0, c_kam)
    # Kamera 2: denize en yakın blok, güneybatıdan – deniz cephesi + güneş alan balkonlar
    hb = next((b for b in bloklar if b["ad"] == KAHRAMAN), min(bloklar, key=lambda b: b["v"]))
    cam2 = kamera("CAM_BLOK", (hb["u"] - 34.0, hb["v"] - 60.0, 17.0),
                  (hb["u"] - 1.0, hb["v"] + 2.0, 10.5), 50.0, c_kam)
    # Kamera 3: aynı blok, batıdan – yan cephe: balkonlar, sürgülü camlar, Fransız camlı salonlar
    cam3 = kamera("CAM_YAN", (hb["u"] - 48.0, hb["v"] - 30.0, 24.0),
                  (hb["u"] - 6.0, hb["v"] + 1.0, 11.5), 44.0, c_kam)

    peyzaj(M, c_peyzaj, bloklar, agac, c_peyzaj)
    arazi = deniz_ve_arazi(M, c_cevre)
    orman_gn(arazi, agac["ORMAN"])
    ev_sayisi, arac_sayisi = cevre(M, c_cevre, agac, c_cevre, araclar,
                                   [tuple(cam2.location.xy), tuple(cam3.location.xy)])
    rapor(bloklar)
    sc.world = isik(c_kam)

    # kamera dibindeki ağaçları kaldır (ön planda kaba görünmesin)
    for ob in list(c_cevre.objects) + list(c_peyzaj.objects):
        ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
        if ic and ic.name.startswith("AGAC") and \
                ((ob.location.xy - cam2.location.xy).length < 42.0 or
                 (ob.location.xy - cam3.location.xy).length < 30.0):
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


def render_al(sc, sc2, sadece_yan=False):
    os.makedirs(CIKTI_KLASORU, exist_ok=True)
    n = sum(d["adet"] for d in DIZI.values())
    isler = [(sc2, "CAM_YAN", f"03_yalova_{n}blok_yan_cephe.png")]
    if not sadece_yan:
        isler = [(sc, "CAM_GENEL", f"01_yalova_{n}blok_genel.png"),
                 (sc2, "CAM_BLOK", f"02_yalova_{n}blok_tek_blok.png")] + isler
    for s, kam, dosya in isler:
        s.camera = bpy.data.objects[kam]
        s.render.filepath = os.path.join(CIKTI_KLASORU, dosya)
        bpy.ops.render.render(write_still=True, scene=s.name)
        print("Kaydedildi:", s.render.filepath)
    sc2.camera = bpy.data.objects["CAM_BLOK"]


if __name__ == "__main__":
    gc.disable()                         # yüz binlerce geometri listesi: kurulumu hızlandırır
    try:
        _sc, _sc2 = kur()
    finally:
        gc.enable()
    if OTOMATIK_RENDER:
        render_al(_sc, _sc2, SADECE_YAN)
