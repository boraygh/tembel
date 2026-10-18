# -*- coding: utf-8 -*-
"""
YALOVA · ARMUTLU · KARŞIYAKA MAH. (Tavşantepe Mevkii, Pafta 39/2)
PARSEL 7104 (5.648 m²) + 7105 (4.510 m²)
27 BLOK · ZEMİN+5 = 6 KAT · KATTA 2 DAİRE  ->  324 DAİRE   (taslak kütle + render)

Blender 4.2 – 5.x · Cycles
Arayüzden : Scripting sekmesi > Open > bu dosya > Run Script
            İki sahne kurulur: "YALOVA_GENEL" (tüm proje) ve "YALOVA_TEK_BLOK" -> F12
Konsoldan : blender -b -P yalova_armutlu_27blok.py -- --render  [--cikti KLASOR]

Parsel köşeleri TKGM parsel sorgusundan, kıyı/yollar uydu görüntüsünden ölçeklendi.
Koordinat sistemi parsel eksenine hizalı: +Y = parsel boyu (denizden uzağa), deniz -Y yönünde.
Gerçek kuzey bu eksenin 17° batısında; güneş buna göre hesaplanıyor.
"""
import bpy
import math
import os
import random
import sys

import numpy as np
from mathutils import Vector, noise

# ============================== AYARLAR ==============================
CIKTI_KLASORU = os.path.join(os.path.expanduser("~"), "Yalova_Armutlu_Render")
OTOMATIK_RENDER = False          # True -> iki PNG'yi render alıp CIKTI_KLASORU'na yazar
ORNEK = 256                      # Cycles sample (GPU'da 256-512 rahat)
COZ_GENEL = (2560, 1440)         # tüm proje
COZ_BLOK = (1600, 2000)          # tek blok (4:5 dikey)
GUNES_AZIMUT = 236.0             # derece, kuzeyden saat yönünde (236 = GB, ikindi güneşi)
GUNES_YUKSEKLIK = 26.0           # derece
TOHUM = 11                       # komşu ev / ağaç dağılımı

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

# =========================== PALET (sRGB HEX) ===========================
# Sancaktepe'de kullandığınız kodlar varsa bu satırlara birebir yazın; tüm sahne günceller.
PALET = {
    "beyaz":       "#ECE8E1",   # döşeme alınları, yüzer saçak – sıcak beyaz kompozit
    "traverten":   "#CDBDA2",   # cephe kaplama – açık traverten
    "antrasit":    "#2C2E31",   # çekirdek kulesi, saksılar
    "kaide":       "#3D3A36",   # zemin kaidesi – bazalt
    "bronz":       "#8E6C49",   # doğrama, dikey fin, küpeşte – şampanya bronz
    "ahsap":       "#7B4A2B",   # teras tavanları, saçak altı – tik
    "cam":         "#24323A",   # cephe camı – füme, yansıtıcı
    "korkuluk":    "#E4F2EE",   # çerçevesiz cam korkuluk
    "tas":         "#D9D1C3",   # teras / peyzaj taşı
    "yesil":       "#4C6B2E",   # çit, saksı bitkisi
    "cati_yesil":  "#6E7F3C",   # yeşil çatı (sedum)
    "cim":         "#6F8F3A",
    "havuz":       "#5EC8D2",
    "deniz_kiyi":  "#4FB3AE",
    "deniz_sig":   "#1F7F8C",
    "deniz_derin": "#0C3A55",
    "kum":         "#BDAA86",   # çakıllı kumsal
    "asfalt":      "#3B3C3E",
    "kaldirim":    "#B8B3AA",
    "ev_duvar":    "#DDD5C6",
    "ev_cati":     "#B3573A",   # mevcut yazlıklar – kiremit
    "arazi":       "#8A8A55",
    "orman":       "#34492A",
    "yaprak":      "#3F5C2A",
    "zeytin":      "#7A8A63",
    "palmiye":     "#4E6B2C",
    "govde":       "#5A4634",
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


class Govde:
    """Basit mesh toplayıcı: kutu / prizma / şerit -> tek obje, malzeme slotlu."""

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


def _gurultu(nt, vec, olcek, detay=6.0):
    nz = nt.nodes.new("ShaderNodeTexNoise")
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


def mat_duz(ad, hexr, rough=0.5, metal=0.0, spec=0.5, coat=0.0, var=0.06, olcek=1.5,
            bump=0.0, bump_olcek=None, koord="Object"):
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
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_traverten(hexr):
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
    nt.links.new(_rampa(nt, fac, [(0.25, _kat(c, 0.88)), (0.55, c), (0.85, _kat(c, 1.07))]),
                 p.inputs["Base Color"])
    _bump(nt, p, _gurultu(nt, vec, 45.0, 3.0), 0.06, 0.01)
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


def mat_cam(hexr):
    m, nt, out = _yeni_mat("Cephe_Cami")
    p = _bsdf(nt, renk(hexr), rough=0.015, spec=0.6, coat=1.0)
    _ata(p, 0.0, "Coat Roughness", "Clearcoat Roughness")
    _bump(nt, p, _gurultu(nt, _koord(nt), 0.25, 2.0), 0.012, 0.2)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_seffaf(ad, hexr, ior=1.5, olcek=0.0, guc=0.0):
    m, nt, out = _yeni_mat(ad)
    p = _bsdf(nt, renk(hexr), rough=0.0, trans=1.0, ior=ior)
    if guc > 0:
        _bump(nt, p, _gurultu(nt, _koord(nt, "Position"), olcek, 3.0), guc, 0.05)
    _golge_seffaf(nt, out, p.outputs[0])
    return m


def mat_bitki(ad, hexr, olcek=2.5):
    m, nt, out = _yeni_mat(ad)
    c = renk(hexr)
    p = _bsdf(nt, c, 0.75, spec=0.3)
    vec = _koord(nt)
    fac = _gurultu(nt, vec, olcek, 5.0)
    nt.links.new(_rampa(nt, fac, [(0.3, _kat(c, 0.6)), (0.55, c), (0.75, _kat(c, 1.35))]),
                 p.inputs["Base Color"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    _ata(vor, olcek * 4.0, "Scale")
    nt.links.new(vec, vor.inputs["Vector"])
    _bump(nt, p, vor.outputs["Distance"], 0.45, 0.1)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_deniz():
    m, nt, out = _yeni_mat("Deniz")
    p = _bsdf(nt, renk(PALET["deniz_derin"]), rough=0.06, spec=0.5, ior=1.333)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "kiyi"
    derin = renk(PALET["deniz_derin"])
    nt.links.new(_rampa(nt, at.outputs["Fac"], [(0.0, renk(PALET["deniz_kiyi"])),
                                                 (0.22, renk(PALET["deniz_sig"])),
                                                 (0.6, _kat(derin, 1.15)),
                                                 (1.0, _kat(derin, 0.8))]),
                 p.inputs["Base Color"])
    pos = _koord(nt, "Position")
    d1 = _gurultu(nt, pos, 0.045, 6.0)
    d2 = _gurultu(nt, pos, 0.5, 4.0)
    d3 = _gurultu(nt, pos, 2.6, 2.0)
    h = _matematik(nt, 'MULTIPLY_ADD', d2, 0.45, d1)
    _bump(nt, p, _matematik(nt, 'MULTIPLY_ADD', d3, 0.12, h), 0.55, 0.6)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_komsu_duvar(renkler):
    """Komşu evler: ev başına ton + prosedürel pencere düzeni."""
    m, nt, out = _yeni_mat("Komsu_Duvar")
    p = _bsdf(nt, renkler[0], 0.75, spec=0.3)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "ton"
    n = len(renkler) - 1
    duvar = _rampa(nt, at.outputs["Fac"], [(i / n, c) for i, c in enumerate(renkler)])
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
    rmix = _matematik(nt, 'MULTIPLY_ADD', maske, -0.6, 0.75)
    nt.links.new(rmix, p.inputs["Roughness"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_arazi():
    """Kıyıda kum, düzlükte kuru çim, yamaçta orman + uzak mesafe pusu."""
    m, nt, out = _yeni_mat("Arazi")
    p = _bsdf(nt, renk(PALET["arazi"]), 0.92, spec=0.3)
    pos = _koord(nt, "Position")
    g1 = _gurultu(nt, pos, 0.012, 6.0)
    zemin = _rampa(nt, g1, [(0.35, renk("#6E7C3E")), (0.5, renk(PALET["arazi"])),
                            (0.68, renk("#A49A66"))])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(pos, sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value, mr.inputs[2].default_value = 3.0, 30.0
    nt.links.new(sep.outputs[2], mr.inputs[0])
    g2 = _gurultu(nt, pos, 0.006, 8.0)
    orman_c = renk(PALET["orman"])
    orman = _rampa(nt, g2, [(0.38, _kat(orman_c, 0.62)), (0.52, orman_c),
                            (0.66, _kat(orman_c, 1.25)), (0.74, renk("#6E7448"))])
    c = _karistir(nt, mr.outputs[0], zemin, orman)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "kumsal"
    c = _karistir(nt, at.outputs["Fac"], c, renk(PALET["kum"]))
    cam = nt.nodes.new("ShaderNodeCameraData")
    pus = nt.nodes.new("ShaderNodeMapRange")
    pus.inputs[1].default_value, pus.inputs[2].default_value = 600.0, 4000.0
    pus.inputs[3].default_value, pus.inputs[4].default_value = 0.0, 0.45
    nt.links.new(cam.outputs["View Distance"], pus.inputs[0])
    c = _karistir(nt, pus.outputs[0], c, renk("#A9B8C4"))
    nt.links.new(c, p.inputs["Base Color"])
    # yamaçta ağaç tepeleri, düzlükte ince çim pürüzü
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    _ata(vor, 0.18, "Scale")
    nt.links.new(pos, vor.inputs["Vector"])
    ince = _gurultu(nt, pos, 3.0, 4.0)
    h = _matematik(nt, 'MULTIPLY', vor.outputs["Distance"], mr.outputs[0])
    _bump(nt, p, _matematik(nt, 'MULTIPLY_ADD', ince, 0.08, h), 0.4, 1.0)
    nt.links.new(p.outputs[0], out.inputs["Surface"])
    return m


def mat_tonlu(ad, renkler, rough=0.7):
    """Komşu evler: ev başına farklı ton ('ton' attribute)."""
    m, nt, out = _yeni_mat(ad)
    p = _bsdf(nt, renkler[0], rough, spec=0.35)
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "ton"
    n = len(renkler) - 1
    nt.links.new(_rampa(nt, at.outputs["Fac"], [(i / n, c) for i, c in enumerate(renkler)]),
                 p.inputs["Base Color"])
    nt.links.new(p.outputs[0], out.inputs["Surface"])
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
    return {
        "beyaz": mat_duz("Beyaz_Kompozit", P["beyaz"], 0.42, var=0.03),
        "traverten": mat_traverten(P["traverten"]),
        "antrasit": mat_duz("Antrasit", P["antrasit"], 0.38, coat=0.15, var=0.05),
        "kaide": mat_duz("Bazalt_Kaide", P["kaide"], 0.6, var=0.12, olcek=3, bump=0.1),
        "bronz": mat_duz("Sampanya_Bronz", P["bronz"], 0.30, metal=1.0, var=0.04),
        "ahsap": mat_ahsap(P["ahsap"]),
        "cam": mat_cam(P["cam"]),
        "korkuluk": mat_seffaf("Cam_Korkuluk", P["korkuluk"]),
        "tas": mat_karo("Tas_Kaplama", P["tas"], 0.6),
        "yesil": mat_bitki("Bitki_Cit", P["yesil"]),
        "cati_yesil": mat_bitki("Yesil_Cati", P["cati_yesil"], 4.0),
        "cim": mat_duz("Cim", P["cim"], 0.9, spec=0.3, var=0.22, olcek=0.35, bump=0.25,
                       bump_olcek=25.0),
        "havuz": mat_karo("Havuz_Seramik", P["havuz"], 0.25, rough=0.25),
        "su": mat_seffaf("Havuz_Suyu", "#DDF6F4", 1.333, 1.8, 0.10),
        "asfalt": mat_duz("Asfalt", P["asfalt"], 0.85, spec=0.3, var=0.10, olcek=0.6, bump=0.08,
                          bump_olcek=30.0),
        "kaldirim": mat_karo("Kaldirim", P["kaldirim"], 0.4, 0.75),
        "deniz": mat_deniz(),
        "arazi": mat_arazi(),
        "ev_duvar": mat_komsu_duvar([renk("#D9D2C4"), renk(P["ev_duvar"]),
                                     renk("#CDBB98"), renk("#D6C3B2")]),
        "ev_cati": mat_tonlu("Komsu_Cati", [renk("#9E4A30"), renk(P["ev_cati"]),
                                            renk("#C06A45"), renk("#8C4630")], 0.65),
        "duz_cati": mat_duz("Duz_Cati", "#BDB8AE", 0.8, var=0.1),
        "iskele": mat_duz("Iskele", "#C9C2B4", 0.8, var=0.1, olcek=2),
        "tekne": mat_duz("Tekne", "#F4F4F2", 0.25, coat=0.6, var=0.0),
        "yaprak": mat_bitki("Agac_Yaprak", P["yaprak"], 1.6),
        "zeytin": mat_bitki("Zeytin_Yaprak", P["zeytin"], 1.8),
        "palmiye": mat_bitki("Palmiye_Yaprak", P["palmiye"], 2.0),
        "govde": mat_duz("Agac_Govde", P["govde"], 0.85, var=0.15, olcek=4),
    }


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

    # ara döşemeler: beyaz alın, tik tavan, çerçevesiz cam korkuluk, saksı
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
def agac_tipleri(M, ust):
    tipler = {}

    def yeni(ad):
        c = koleksiyon(ad, ust)
        tipler[ad] = c
        return c

    g = Govde()
    g.prizma([(0.22 * math.cos(a * math.pi / 4), 0.22 * math.sin(a * math.pi / 4)) for a in range(8)],
             0, 2.8, M["govde"])
    g.kure((0, 0, 4.4), (2.6, 2.5, 2.1), M["yaprak"], 14, 9, 0.28, 1.0)
    g.kure((0.9, 0.6, 5.6), (1.6, 1.5, 1.3), M["yaprak"], 10, 7, 0.25, 4.0)
    g.obje("agac_yuvarlak", yeni("AGAC_YUVARLAK"))

    g = Govde()
    g.prizma([(0.2 * math.cos(a * math.pi / 3), 0.2 * math.sin(a * math.pi / 3)) for a in range(6)],
             0, 1.7, M["govde"])
    g.kure((0, 0, 2.7), (1.9, 1.8, 1.25), M["zeytin"], 12, 8, 0.32, 2.0)
    g.obje("zeytin", yeni("AGAC_ZEYTIN"))

    g = Govde()
    g.prizma([(0.15 * math.cos(a * math.pi / 3), 0.15 * math.sin(a * math.pi / 3)) for a in range(6)],
             0, 1.0, M["govde"])
    g.kure((0, 0, 4.4), (0.85, 0.85, 4.0), M["yaprak"], 10, 9, 0.12, 3.0)
    g.obje("servi", yeni("AGAC_SERVI"))

    g = Govde()
    H = 7.2
    for k in range(7):                       # hafif kıvrık gövde
        z0, z1 = H * k / 7, H * (k + 1) / 7
        r = 0.26 - 0.012 * k
        ox = 0.35 * (k / 7) ** 2
        g.prizma([(ox + r * math.cos(a * math.pi / 4), r * math.sin(a * math.pi / 4))
                  for a in range(8)], z0, z1, M["govde"], ust=False, alt=False)
    top = (0.35, 0.0, H)
    for k in range(11):                      # yapraklar
        a = 2 * math.pi * k / 11 + 0.3 * math.sin(k * 2.1)
        ca, sa = math.cos(a), math.sin(a)
        b = len(g.v)
        sira = []
        for s in range(6):
            t = s / 5
            L = 3.6 * t
            z = H + 0.9 * t - 2.4 * t * t
            w = 0.55 * (1 - t) + 0.08
            cx, cy = top[0] + ca * L, top[1] + sa * L
            sira += [(cx - sa * w, cy + ca * w, z), (cx + sa * w, cy - ca * w, z - 0.12 * t)]
        g._v(sira)
        for s in range(5):
            q = b + 2 * s
            g.yuz((q, q + 1, q + 3, q + 2), M["palmiye"])
    g.kure(top, (0.45, 0.45, 0.35), M["palmiye"], 8, 5)
    g.obje("palmiye", yeni("AGAC_PALMIYE"))
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
_KP = np.stack([KU[::3], KV[::3]], 1)


def kiyi_v(u):
    return np.interp(u, KU, KV)


def kiyi_d(u, v):
    """Kıyı çizgisine en kısa mesafe (m); kara tarafı +, deniz tarafı -."""
    u, v = np.asarray(u, dtype=float), np.asarray(v, dtype=float)
    shp, uu, vv = u.shape, u.reshape(-1), v.reshape(-1)
    d = np.empty_like(uu)
    for s in range(0, len(uu), 3000):
        du = uu[s:s + 3000, None] - _KP[None, :, 0]
        dv = vv[s:s + 3000, None] - _KP[None, :, 1]
        d[s:s + 3000] = np.sqrt((du * du + dv * dv).min(1))
    isaret = np.where(vv >= np.interp(uu, KU, KV), 1.0, -1.0)
    return (d * isaret).reshape(shp)


def _kolonlar():
    ince = np.arange(-460.0, 660.0, 5.0)
    kaba_b = np.array([-3000, -2400, -1800, -1350, -1000, -750, -580])
    kaba_d = np.array([800, 1000, 1300, 1700, 2200, 2700, 3000])
    return np.concatenate([kaba_b, ince, kaba_d]).astype(float)


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
    t = smooth(400.0, 1300.0, D)
    tepe = np.zeros_like(U)
    idx = np.nonzero(t > 0)
    for i, j in zip(*idx):
        u, v = U[i, j], V[i, j]
        n1 = noise.noise(Vector((u / 700.0, v / 700.0, 0.3)))
        n2 = noise.noise(Vector((u / 210.0, v / 210.0, 2.1)))
        tepe[i, j] = 210.0 + 130.0 * n1 + 40.0 * n2
    return Z + t * tepe


def deniz_ve_arazi(M, coll):
    us = _kolonlar()
    kara = np.array([-8, -5, -2.5, 0, 2.5, 5, 7.5, 10, 12.5, 15, 18, 22, 27, 33, 40, 48, 57, 67,
                     78, 90, 105, 120, 140, 160, 185, 210, 240, 270, 305, 340, 380, 420, 460,
                     505, 555, 610, 680, 760, 850, 950, 1070, 1210, 1370, 1550, 1750, 1970, 2220,
                     2500, 2800, 3150, 3550, 4000], dtype=float)
    _grid_mesh("ARAZI", us, kara, arazi_z,
               {"kumsal": lambda U, V, D: 1.0 - smooth(6.0, 10.0, D)}, M["arazi"], coll)
    deniz = np.array([5, 1, -1, -3, -5, -8, -11, -15, -20, -26, -33, -41, -50, -60, -72, -86,
                      -102, -122, -146, -175, -210, -255, -310, -380, -470, -580, -720, -900,
                      -1150, -1500, -2000, -2700, -3600], dtype=float)
    _grid_mesh("DENIZ", us, deniz, lambda U, V, D: np.full_like(U, -0.25),
               {"kiyi": lambda U, V, D: np.clip(-D / 55.0, 0.0, 1.0) ** 0.7}, M["deniz"], coll)


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
        (SAHIL_YOLU, 8.0, "proje"),
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


def _sahil_v(u):
    xs = [p[0] for p in SAHIL_YOLU]
    if u < xs[0] or u > xs[-1]:
        return None
    return float(np.interp(u, xs, [p[1] for p in SAHIL_YOLU]))


def cevre(M, coll, agac, agac_coll):
    rnd = random.Random(TOHUM)
    yol = Govde()
    kirpik = []
    for i, (pts, gen, tur) in enumerate(_yol_listesi()):
        p = _kirp(pts)
        if len(p) < 2:
            continue
        p = p[::3] + ([p[-1]] if (len(p) - 1) % 3 else [])
        xs, ys = [q[0] for q in p], [q[1] for q in p]
        kirpik.append((p, gen, (min(xs), max(xs), min(ys), max(ys))))
        yol.yatay_serit(p, gen, 0.020 + 0.0004 * i, M["asfalt"])
    # proje parsellerinin çevresinde kaldırım
    for poly in (P7104, P7105):
        for p in _kenar_parcalari(poly, -0.85):
            yol.serit(p, 0.0, 0.14, 1.7, M["kaldirim"])
    # sahil parkı: yürüyüş yolu + palmiyeler + iskeleler
    us = np.arange(-170.0, 300.0, 4.0)
    promenat = [(float(u), float(kiyi_v(u) + 17.0)) for u in us]
    yol.yatay_serit(promenat, 3.0, 0.03, M["kaldirim"])
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
    yol.obje("YOLLAR_SAHIL", coll)

    # tekneler
    t = Govde()
    for (u, v, r, L) in ((25.0, -150.0, 0.5, 12.0), (112.0, -106.0, -0.4, 9.0),
                         (-20.0, -162.0, 1.0, 14.0)):
        c, s = math.cos(r), math.sin(r)
        tekne = [(-L / 2, -1.4), (L * 0.25, -1.5), (L / 2, 0.0), (L * 0.25, 1.5), (-L / 2, 1.4)]
        kab = [(-L * 0.3, -1.0), (L * 0.1, -1.0), (L * 0.1, 1.0), (-L * 0.3, 1.0)]
        rot = lambda P: [(u + x * c - y * s, v + x * s + y * c) for x, y in P]
        t.prizma(rot(tekne), -0.5, 0.6, M["tekne"])
        t.prizma(rot(kab), 0.6, 1.7, M["tekne"])
    t.obje("TEKNELER", coll)

    # Samanyolu Sk. doğusundaki mevcut sıra yazlıklar
    ev = Govde()
    cati = Govde()

    def ev_ekle(x0, x1, y0, y1, kat_say, kirma=True):
        H = 3.0 * kat_say + 0.3
        ev._t = cati._t = rnd.random()
        ev.kutu(x0, x1, y0, y1, 0.0, H, M["ev_duvar"], ust=None if not kirma else False,
                alt=False)
        if kirma:
            cati.kirma_cati(x0, x1, y0, y1, H, min(x1 - x0, y1 - y0) * 0.28, M["ev_cati"])
        else:
            ev.kutu(x0 + 0.3, x1 - 0.3, y0 + 0.3, y1 - 0.3, H, H + 0.05, M["duz_cati"], alt=False)
        return (x0, x1, y0, y1)

    evler = []
    v = -50.0
    while v < 72:
        ue = _kenar_u(P7105, min(max(v, -64.0), 73.0), 1) + 9.0
        kay = 0.8 if int((v + 50) / 7.6) % 2 else 0.0
        evler.append(ev_ekle(ue + kay, ue + kay + 11.0, v, v + 7.3, 2))
        v += 7.6

    # komşu dokusu: sokak ızgarasına oturan parseller
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
        if any(bb[0] - 20 < uc < bb[1] + 20 and bb[2] - 20 < vc < bb[3] + 20 and
               _nokta_cizgi(uc, vc, p) < g / 2 + r_ic + 1.0 for p, g, bb in kirpik):
            continue
        if rnd.random() < 0.28:
            for _ in range(rnd.randint(2, 5)):
                tip = rnd.choice(("AGAC_YUVARLAK", "AGAC_ZEYTIN", "AGAC_YUVARLAK", "AGAC_SERVI"))
                ornekle("agac", agac[tip], agac_coll,
                        (uc + rnd.uniform(-6, 6), vc + rnd.uniform(-6, 6), 0.0),
                        rnd.uniform(0, 6.28), rnd.uniform(0.7, 1.2))
            continue
        evler.append(ev_ekle(uc - w / 2, uc + w / 2, vc - dd / 2, vc + dd / 2,
                             rnd.choice((2, 2, 3)), rnd.random() < 0.78))
        for _ in range(rnd.choice((1, 1, 2, 2, 3))):
            tip = rnd.choice(("AGAC_YUVARLAK", "AGAC_ZEYTIN", "AGAC_SERVI", "AGAC_YUVARLAK"))
            ku = uc + math.copysign(w / 2 + rnd.uniform(2.0, 3.5), rnd.uniform(-1, 1))
            ornekle("agac", agac[tip], agac_coll, (ku, vc + rnd.uniform(-5, 5), 0.0),
                    rnd.uniform(0, 6.28), rnd.uniform(0.7, 1.15))
    ev.obje("KOMSU_EVLER", coll, ton_attr=True)
    cati.obje("KOMSU_CATILAR", coll, ton_attr=True)

    # sahil parkı ve proje güneyi: dağınık ağaçlar
    for _ in range(140):
        u = rnd.uniform(-180, 300)
        d = rnd.uniform(20, 70)
        v = float(kiyi_v(u)) + d
        sv = _sahil_v(u)
        if sv is not None and v > sv - 6:
            v = sv - rnd.uniform(8, 20)
            if float(kiyi_d(u, v)) < 18:
                continue
        tip = rnd.choice(("AGAC_YUVARLAK", "AGAC_ZEYTIN", "AGAC_PALMIYE"))
        ornekle("agac", agac[tip], agac_coll, (u, v, 0.0), rnd.uniform(0, 6.28),
                rnd.uniform(0.75, 1.15))
    # yerleşimin tepeye geçtiği bant: sık ağaçlık
    for _ in range(320):
        u = rnd.uniform(-460.0, 650.0)
        v = float(kiyi_v(u)) + rnd.uniform(385.0, 470.0)
        z = float(arazi_z(np.array([[u]]), np.array([[v]]), kiyi_d(np.array([[u]]), np.array([[v]])))[0, 0])
        tip = rnd.choice(("AGAC_YUVARLAK", "AGAC_YUVARLAK", "AGAC_SERVI", "AGAC_ZEYTIN"))
        ornekle("agac", agac[tip], agac_coll, (u, v, z - 0.3), rnd.uniform(0, 6.28),
                rnd.uniform(0.8, 1.3))
    return len(evler)


# ============================== IŞIK / KAMERA / RENDER ==============================
def _gunes_yonu():
    az, el = math.radians(GUNES_AZIMUT), math.radians(GUNES_YUKSEKLIK)
    e, n = math.sin(az), math.cos(az)                  # gerçek doğu / kuzey
    th = math.radians(KUZEY_SAPMA)
    u = e * math.cos(th) - n * math.sin(th)
    v = e * math.sin(th) + n * math.cos(th)
    return Vector((u * math.cos(el), v * math.cos(el), math.sin(el))).normalized()


def isik(coll):
    d = _gunes_yonu()
    w = bpy.data.worlds.new("YALOVA_GOKYUZU")
    if w.node_tree is None:
        w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
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
    ld = bpy.data.lights.new("GUNES", 'SUN')
    ld.energy = 4.2
    ld.angle = math.radians(0.8)
    ld.color = (1.0, 0.90, 0.78)
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
    cy.adaptive_threshold = 0.025
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces = 10, 3, 4
    cy.transmission_bounces, cy.transparent_max_bounces = 8, 16
    cy.caustics_reflective = cy.caustics_refractive = False
    cy.blur_glossy = 0.8
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
    sc.view_settings.exposure = 0.0


# ============================== ANA AKIŞ ==============================
def kur():
    sc = sahneyi_temizle()
    sc.name = "YALOVA_GENEL"
    sc.unit_settings.system = 'METRIC'
    M = malzemeler()

    # tip koleksiyonları sahneye bağlanmaz; örnekler (instance) üzerinden render'a girer
    # (düzenlemek için: Outliner > Blender File > Collections > TIP_BLOK)
    c_tip = bpy.data.collections.new("TIP_BLOK")
    c_agac_tip = bpy.data.collections.new("TIP_AGAC")
    c_proje = koleksiyon("PROJE_27_BLOK")
    c_peyzaj = koleksiyon("PEYZAJ")
    c_cevre = koleksiyon("CEVRE_DENIZ")
    c_kam = koleksiyon("KAMERA_ISIK")

    blok_tipi(M, c_tip)
    agac = agac_tipleri(M, c_agac_tip)
    bloklar = yerlesim()
    c_7104 = koleksiyon("PARSEL_7104", c_proje)
    c_7105 = koleksiyon("PARSEL_7105", c_proje)
    for b in bloklar:
        ornekle("BLOK_" + b["ad"], c_tip, c_7104 if b["parsel"] == "7104" else c_7105,
                (b["u"], b["v"], 0.0))
    peyzaj(M, c_peyzaj, bloklar, agac, c_peyzaj)
    deniz_ve_arazi(M, c_cevre)
    ev_sayisi = cevre(M, c_cevre, agac, c_cevre)
    rapor(bloklar)

    w = isik(c_kam)
    sc.world = w
    # Kamera 1: denizden, güneydoğudan kuşbakışı – tüm proje
    cam1 = kamera("CAM_GENEL", (138.0, -221.0, 70.0), (22.4, -46.0, 0.0), 35.0, c_kam)
    # Kamera 2: denize en yakın, deniz aksına bakan blok (7104-B1) – tek blok
    hb = next(b for b in bloklar if b["ad"] == "7104-B1")
    cam2 = kamera("CAM_BLOK", (hb["u"] + 30.0, hb["v"] - 50.0, 25.0),
                  (hb["u"] - 1.5, hb["v"] + 0.5, 9.0), 55.0, c_kam)
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
    sc2.world = w
    sc2.camera = cam2
    sc2.unit_settings.system = 'METRIC'
    render_ayari(sc2, COZ_BLOK, gpu)
    print(f"Komşu ev: {ev_sayisi}  |  Render cihazı: {'GPU' if gpu else 'CPU'}")
    return sc, sc2


def render_al(sc, sc2):
    os.makedirs(CIKTI_KLASORU, exist_ok=True)
    for s, dosya in ((sc, "01_yalova_armutlu_genel.png"), (sc2, "02_yalova_armutlu_tek_blok.png")):
        s.render.filepath = os.path.join(CIKTI_KLASORU, dosya)
        bpy.ops.render.render(write_still=True, scene=s.name)
        print("Kaydedildi:", s.render.filepath)


if __name__ == "__main__":
    _sc, _sc2 = kur()
    if OTOMATIK_RENDER:
        render_al(_sc, _sc2)
