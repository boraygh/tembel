# Görsel 14'ün açısı (CAM_GENEL konumu ve hedefi), 42 mm ile ~%20 yakın; v4 tasarım (5 kat, #302B27 silmeler).
# Kullanım: blender -b --factory-startup -P genel_yakin3.py -- [--onizle] [--ornek N] [--maske]
# Maske sonrası girdi: ../video/araclar/girdi_yap.py, filigran: ../video/araclar/filigran.py
import sys, os, json, runpy, gc
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONIZLE, MASKE = "--onizle" in arg, "--maske" in arg
ORNEK = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 256
COZ = (960, 540) if ONIZLE else (2560, 1440)
sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(OUT, "..", "yalova_armutlu_16blok.py"), run_name="y3")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
cam = ns["kamera"]("CAM_YAKIN3", (138.0, -221.0, 70.0), (22.4, -46.0, 0.0), 42.0, bpy.data.collections["KAMERA_ISIK"])
# yat kadrajın alt kenarında kesilmesin: 12 m kıyıya doğru (hâlâ denizde, kıyıya ~25 m)
t = bpy.data.objects["TEKNELER"]
assert t.matrix_world.is_identity
for v in t.data.vertices:
    if (v.co.x - 112.0) ** 2 + (v.co.y + 106.0) ** 2 < 81.0:
        v.co.x -= 7.8
        v.co.y += 9.1
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = COZ
if not MASKE:
    sc.cycles.samples = 16 if ONIZLE else ORNEK
    sc.render.filepath = os.path.join(OUT, ("oniz_" if ONIZLE else "") + "yakin3_render.png")
    bpy.ops.render.render(write_still=True, scene=sc.name)
    print("render tamam", flush=True)
    sys.exit(0)

# ---- yumuşatma maskesi: beyaz = komşu evler + tüm ağaçlar (proje bahçesi ve sahil parkı dahil) ----
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
kiyi_d = ns["kiyi_d"]
for ob in bpy.data.objects:                       # yalnız kumsaldaki ağaçlar keskin kalır
    ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
    if ic and ic.name.startswith("AGAC") and float(kiyi_d(ob.location.x, ob.location.y)) < 12.0:
        ob.is_holdout = True

def holdout(lc, aktif=False):                     # proje binaları (balkon bitkileri dahil) korunur
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
sc.render.filepath = os.path.join(OUT, "yakin3_maske.png")
bpy.ops.render.render(write_still=True, scene=sc.name)
# su kenarının 14 m kara tarafı: bunun altı (kumsal + deniz) hiç yumuşatılmaz
kiyi_v = ns["kiyi_v"]
W, H = COZ
hat = []
for k in range(-160, 241):
    u = k * 2.5
    p = world_to_camera_view(sc, cam, Vector((u, float(kiyi_v(u)) + 14.0, 0.0)))
    if p.z > 0:
        hat.append((p.x * W, (1.0 - p.y) * H))
json.dump(hat, open(os.path.join(OUT, "yakin3_kiyi.json"), "w"))
print("maske tamam", flush=True)
