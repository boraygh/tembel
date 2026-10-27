# 8 + 9 yerleşim: açılış köşe drone karesi (A0) + sol sıranın 8 bloğu için en üst kat güneybatı köşe
# balkonundan deniz manzarası kareleri (S1 = en arka A blok ... S8 = en ön H blok).
# Kullanım: blender -b --factory-startup -P manzara.py -- [--onizle] [--sadece A0,S1] [--ornek N] [--maske]
import sys, os, json, runpy, gc, math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONIZLE, MASKE = "--onizle" in arg, "--maske" in arg
SADECE = arg[arg.index("--sadece") + 1].split(",") if "--sadece" in arg else None
ORNEK = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 160
COZ = (960, 540) if ONIZLE else (1920, 1080)
sys.argv = [sys.argv[0], "--", "--sol", "8", "--sag", "9"]
ns = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "yalova_armutlu_16blok.py"), run_name="manzara")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
coll = bpy.data.collections["KAMERA_ISIK"]
T = ns["BLOK_TIPLERI"]["A264"]
Z0, KAT, KAT_H = ns["Z0"], ns["KAT"], ns["KAT_H"]
GOZ = Z0 + (KAT - 1) * KAT_H + 1.6                      # en üst kat döşemesi + göz yüksekliği
YON = Vector((-math.sin(math.radians(25)), -math.cos(math.radians(25)), 0.0))   # güney-güneybatı (deniz)

# --- kameralar ---
KAM = {}
T0 = Vector((22.4, -46.0, 0.0))                          # köşe görsellerinin hedefi
y0 = Vector((138.0 - 22.4, -221.0 + 46.0, 0.0)).normalized()
D3 = (Vector((138.0, -221.0, 70.0)) - T0).length
e = math.radians(28.0)
KAM["A0"] = dict(konum=tuple(T0 + y0 * D3 * math.cos(e) + Vector((0, 0, D3 * math.sin(e)))),
                 hedef=tuple(T0), lens=42.0, kay=0.0, blok=None)
sol = sorted((o for o in bpy.data.objects if o.name.startswith("BLOK_7104-")), key=lambda o: o.name)
assert len(sol) == 8, [o.name for o in sol]
for i, ob in enumerate(sol):                             # A (kuzey, en arka) ... H (güney, en ön)
    u, v = ob.location.x, ob.location.y
    k = Vector((u - (T["bk"] + T["xb"]) / 2, v - T["yu"] + 1.2, GOZ))   # batı uç balkonunun güney ucu
    KAM[f"S{i + 1}"] = dict(konum=tuple(k), hedef=tuple(k + YON * 100.0), lens=24.0, kay=-0.12,
                           blok=ob.name.replace("BLOK_", ""))
json.dump(KAM, open(os.path.join(OUT, "kameralar.json"), "w"), indent=1)
kams = {}
for ad, k in KAM.items():
    c = ns["kamera"]("MZ_" + ad, k["konum"], k["hedef"], k["lens"], coll)
    c.data.shift_y = k["kay"]
    c.data.clip_start = 0.05
    kams[ad] = c
secili = [a for a in KAM if not SADECE or a in SADECE]
sc.render.resolution_x, sc.render.resolution_y = COZ

if not MASKE:
    for ad in secili:
        sc.camera = kams[ad]
        sc.cycles.samples = 16 if ONIZLE else ORNEK
        sc.render.filepath = os.path.join(OUT, ("oniz_" if ONIZLE else "") + f"{ad}_render.png")
        bpy.ops.render.render(write_still=True, scene=sc.name)
        print("kare", ad, KAM[ad]["blok"], flush=True)
    sys.exit(0)

# ---- yumuşatma maskesi: beyaz = komşu evler + ağaçlar (yeniden çizilir); proje binaları korunur ----
AGAC_EV = {"Agac_Yaprak", "Zeytin_Yaprak", "Cam_Yaprak", "Palmiye_Yaprak", "Agac_Govde",
           "Komsu_Duvar", "Komsu_Kiremit", "Duz_Cati", "Bahce_Duvari", "Gunes_Paneli",
           "Tank_Beyaz", "Tank_Siyah", "Demir_Korkuluk", "Tente"}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    outs = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    if not outs:
        continue
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = 1.0
    v = 1.0 if m.name.split(".")[0] in AGAC_EV else 0.0
    em.inputs[0].default_value = (v, v, v, 1.0)
    for o in outs:
        for l in list(o.inputs["Surface"].links):
            nt.links.remove(l)
        nt.links.new(em.outputs[0], o.inputs["Surface"])
kiyi_d, kiyi_v = ns["kiyi_d"], ns["kiyi_v"]
for ob in bpy.data.objects:                              # kumsaldaki ağaçlar keskin kalır
    ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
    if ic and ic.name.startswith("AGAC") and float(kiyi_d(ob.location.x, ob.location.y)) < 12.0:
        ob.is_holdout = True

def holdout(lc, aktif=False):
    aktif = aktif or lc.name.startswith("PROJE_") or lc.name.startswith("PARSEL_")
    lc.holdout = aktif
    for c in lc.children:
        holdout(c, aktif)
holdout(sc.view_layers[0].layer_collection)
sc.render.film_transparent = True
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.cycles.use_adaptive_sampling = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.render.image_settings.color_mode = 'RGBA'
W, H = COZ
for ad in secili:
    sc.camera = kams[ad]
    sc.render.filepath = os.path.join(OUT, f"{ad}_maske.png")
    bpy.ops.render.render(write_still=True, scene=sc.name)
    hat = []
    for k in range(-200, 281):                           # su kenarının 14 m kara tarafı
        u = k * 2.5
        p = world_to_camera_view(sc, kams[ad], Vector((u, float(kiyi_v(u)) + 14.0, 0.0)))
        if p.z > 0:
            hat.append((p.x * W, (1.0 - p.y) * H))
    json.dump(hat, open(os.path.join(OUT, f"{ad}_kiyi.json"), "w"))
    print("maske", ad, flush=True)
