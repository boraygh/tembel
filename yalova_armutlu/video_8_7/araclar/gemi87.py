# Temsili konteyner gemisi (Blender). gemi(GEMI, koleksiyon) ile sahneye eklenir.
import math, random
import bpy, bmesh
GEMI = dict(merkez=(75.0, -1500.0), aci=197.0, boy=220.0, en=32.0)   # kıyıya paralel, batıya seyir


def malzeme(ad, renk, puruz=0.5, metal=0.0):
    m = bpy.data.materials.new(ad)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*renk, 1.0)
    b.inputs["Roughness"].default_value = puruz
    b.inputs["Metallic"].default_value = metal
    return m


def kutu(bm, x0, x1, y0, y1, z0, z1, mi):
    vs = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    for a, b, c, d in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        f = bm.faces.new((vs[a], vs[b], vs[c], vs[d]))
        f.material_index = mi


def gemi(g, hedef_coll):
    L, B = g["boy"], g["en"]
    s, h = L / 220.0, B / 32.0
    ana = [(-108, -16), (60, -16), (80, -15), (95, -11.5), (104, -6.5), (110, 0), (104, 6.5), (95, 11.5),
           (80, 15), (60, 16), (-108, 16), (-110, 13), (-110, -13)]
    ana = [(x * s, y * h) for x, y in ana]
    renkler = [(0.45, 0.07, 0.05), (0.05, 0.12, 0.32), (0.06, 0.28, 0.12), (0.62, 0.25, 0.04),
               (0.35, 0.36, 0.37), (0.75, 0.74, 0.70), (0.30, 0.05, 0.08), (0.65, 0.48, 0.05)]
    mats = [malzeme("Gemi_Govde", (0.03, 0.045, 0.07), 0.55), malzeme("Gemi_Guverte", (0.16, 0.06, 0.04), 0.7),
            malzeme("Gemi_Ust", (0.85, 0.85, 0.83), 0.4), malzeme("Gemi_Baca", (0.55, 0.10, 0.05), 0.5)] + \
           [malzeme(f"Gemi_Konteyner_{i}", c, 0.65) for i, c in enumerate(renkler)]
    me = bpy.data.meshes.new("GEMI")
    bm = bmesh.new()
    alt = [bm.verts.new((x, y, -9.0)) for x, y in ana]
    ust = [bm.verts.new((x, y, 11.0)) for x, y in ana]
    n = len(ana)
    for i in range(n):
        f = bm.faces.new((alt[i], alt[(i + 1) % n], ust[(i + 1) % n], ust[i]))
        f.material_index = 0
    bm.faces.new(list(reversed(alt))).material_index = 0
    bm.faces.new(ust).material_index = 1
    rnd = random.Random(7)
    x = -76.0 * s
    while x + 12.2 <= 88.0 * s:                          # 40'lık konteyner sıraları, üç blok halinde
        for y0, y1 in ((-13.5, -4.6), (-4.4, 4.4), (4.6, 13.5)):
            kat = rnd.choice((4, 5, 5, 6))
            kutu(bm, x, x + 12.2, y0 * h, y1 * h, 11.0, 11.0 + 2.6 * kat, 4 + rnd.randrange(len(renkler)))
        x += 12.8
    kutu(bm, -100 * s, -86 * s, -15 * h, 15 * h, 11.0, 38.0, 2)       # köşk
    kutu(bm, -92 * s, -86 * s, -17 * h, 17 * h, 34.0, 38.0, 2)        # köprü kanatları
    kutu(bm, -106 * s, -101 * s, -3.5 * h, 3.5 * h, 11.0, 44.0, 3)    # baca
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new("GEMI", me)
    ob.location = (g["merkez"][0], g["merkez"][1], -0.25)
    ob.rotation_euler = (0.0, 0.0, math.radians(g["aci"]))
    hedef_coll.objects.link(ob)
    return ob


