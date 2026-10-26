# Render 27-30 (O1 = ortadan, K2 = köşe; ikisinde de solda 6, sağda 7 blok).
# Revizyon kareleri: ortadan kuşbakışı (iki sıra arasındaki eksen) ve köşe açısı (görsel 14/23 yönü, biraz yüksek).
# Kullanım: blender -b --factory-startup -P ortadan_kose_6x7.py -- --onizle | --sec AD [--ornek N] | --sec AD --maske
import sys, os, json, runpy, gc, math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONIZLE, MASKE = "--onizle" in arg, "--maske" in arg
SEC = arg[arg.index("--sec") + 1] if "--sec" in arg else None
ORNEK = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 512
COZ = (960, 540) if ONIZLE else (3840, 2160)
T0 = Vector((22.4, -46.0, 0.0))                       # görsel 14/23'ün hedef noktası
YON = Vector((138.0 - 22.4, -221.0 + 46.0, 0.0)).normalized()
D3 = (Vector((138.0, -221.0, 70.0)) - T0).length      # 220.9 m


def kose(egim):
    c = T0 + YON * D3 * math.cos(math.radians(egim)) + Vector((0, 0, D3 * math.sin(math.radians(egim))))
    return tuple(c)

ADAY = {   # ad: (kamera, hedef, lens)
    "O1": ((-1.0, -199.0, 147.0), (-1.0, -24.0, 0.0), 35.0),   # ortadan, 40° eğim
    "O2": ((-1.0, -195.0, 117.0), (-1.0, -28.0, 0.0), 32.0),   # ortadan, 35° eğim, biraz daha geniş
    "K1": ((138.0, -221.0, 70.0), (22.4, -46.0, 0.0), 42.0),   # önceki köşe açısı (görsel 23/24)
    "K2": (kose(28.0), (22.4, -46.0, 0.0), 42.0),              # aynı yön ve mesafe, 28° (iki sıra ayrışır)
    "O3": ((-1.0, -278.0, 142.0), (-1.0, -60.0, 0.0), 38.0),   # ortadan, denizin üstünden: altta kumsal ve deniz
}
sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(OUT, "..", "yalova_armutlu_16blok.py"), run_name="orta")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
coll = bpy.data.collections["KAMERA_ISIK"]
# görsel 23'teki gibi yat kadrajın altında kalmasın diye kıyıya 12 m yakın
t = bpy.data.objects["TEKNELER"]
for v in t.data.vertices:
    if (v.co.x - 112.0) ** 2 + (v.co.y + 106.0) ** 2 < 81.0:
        v.co.x -= 7.8
        v.co.y += 9.1
json.dump({k: [list(map(float, a)), list(map(float, b)), c] for k, (a, b, c) in ADAY.items()},
          open(os.path.join(OUT, "kameralar.json"), "w"), indent=1)


def kamera(ad):
    c, h, L = ADAY[ad]
    return ns["kamera"]("REV_" + ad, c, h, L, coll)

sc.render.resolution_x, sc.render.resolution_y = COZ
if ONIZLE:
    for ad in (arg[arg.index("--sadece") + 1].split(",") if "--sadece" in arg else ADAY):
        sc.camera = kamera(ad)
        sc.cycles.samples = 16
        sc.render.filepath = os.path.join(OUT, f"oniz_{ad}.png")
        bpy.ops.render.render(write_still=True, scene=sc.name)
        print("önizleme", ad, flush=True)
    sys.exit(0)

cam = kamera(SEC)
sc.camera = cam
if not MASKE:
    sc.cycles.samples = ORNEK
    sc.render.filepath = os.path.join(OUT, f"{SEC}_render.png")
    bpy.ops.render.render(write_still=True, scene=sc.name)
    print("render tamam", flush=True)
    sys.exit(0)

# ---- maske: komşu evler + bütün ağaçlar beyaz (yeniden çizilir); proje binaları korunur ----
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
for ob in bpy.data.objects:
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
sc.render.filepath = os.path.join(OUT, f"{SEC}_maske.png")
bpy.ops.render.render(write_still=True, scene=sc.name)
W, H = COZ
hat = []
for k in range(-160, 241):
    u = k * 2.5
    p = world_to_camera_view(sc, cam, Vector((u, float(kiyi_v(u)) + 14.0, 0.0)))
    if p.z > 0:
        hat.append((p.x * W, (1.0 - p.y) * H))
json.dump(hat, open(os.path.join(OUT, f"{SEC}_kiyi.json"), "w"))
print("maske tamam", flush=True)
