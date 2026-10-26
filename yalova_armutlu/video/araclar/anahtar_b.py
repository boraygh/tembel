# B seçeneği anahtar kareleri (16:9): K1 yerde, K2-K5 blok 14 m havada, 90°'lik yörünge.
# Kullanım: blender -b --factory-startup -P anahtar_b.py -- [--onizle] [--maske] [--sadece K1,K2]
import sys, os, runpy, gc, json
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
from kamera_b import kameralar
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONIZLE, MASKE = "--onizle" in arg, "--maske" in arg
SADECE = arg[arg.index("--sadece") + 1].split(",") if "--sadece" in arg else None
COZ = (960, 540) if ONIZLE else (1920, 1080)
HOLDOUT_M = float(arg[arg.index("--holdout") + 1]) if "--holdout" in arg else 40.0
KIYI_PAY = float(arg[arg.index("--kiyi_pay") + 1]) if "--kiyi_pay" in arg else None
sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(OUT, "..", "..", "yalova_armutlu_16blok.py"), run_name="b")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
blok = bpy.data.objects["BLOK_7105-G"]
coll = bpy.data.collections["KAMERA_ISIK"]
KAM = {k: v for k, v in kameralar(14.0, 108.0, 58.0, 15.0).items() if not SADECE or k in SADECE}
json.dump(KAM, open(os.path.join(OUT, "kameralar_b.json"), "w"), indent=1)
kams = {ad: ns["kamera"]("B_" + ad, k["konum"], k["hedef"], k["lens"], coll) for ad, k in KAM.items()}

if not MASKE:
    for ad, k in KAM.items():
        blok.location.z = k["kalk"]
        sc2.camera = kams[ad]
        sc2.render.resolution_x, sc2.render.resolution_y = COZ
        if ONIZLE:
            sc2.cycles.samples = 16
        else:
            sc2.cycles.samples = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 160
        sc2.render.filepath = os.path.join(OUT, ("oniz_" if ONIZLE else "") + ad + "_render.png")
        bpy.ops.render.render(write_still=True, scene=sc2.name)
        print("kare", ad, flush=True)
    blok.location.z = 0.0
    sys.exit(0)

# ---- yumuşatma maskeleri: beyaz = yapay zekânın yeniden çizeceği (ağaç, komşu ev, araç, insan) ----
YUMUSAK = {"Agac_Yaprak", "Zeytin_Yaprak", "Cam_Yaprak", "Palmiye_Yaprak", "Agac_Govde",
           "Komsu_Duvar", "Komsu_Kiremit", "Duz_Cati", "Bahce_Duvari", "Gunes_Paneli",
           "Tank_Beyaz", "Tank_Siyah", "Demir_Korkuluk", "Tente", "Bitki_Cit", "Ten", "Kumas",
           "Semsiye", "Araba_Cami", "Lastik"}
emis, adlar = {}, set()
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    outs = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    if not outs:
        continue
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = 1.0
    for o in outs:
        for l in list(o.inputs["Surface"].links):
            nt.links.remove(l)
        nt.links.new(em.outputs[0], o.inputs["Surface"])
    ad = m.name.split(".")[0]
    adlar.add(ad)
    beyaz = ad in YUMUSAK or ad.startswith("Araba_")
    em.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0) if beyaz else (0.0, 0.0, 0.0, 1.0)
print("MALZEMELER:", sorted(adlar), flush=True)
kiyi_d = ns["kiyi_d"]
for ob in bpy.data.objects:                  # yalnız kumsaldaki ağaçlar (kıyıya HOLDOUT_M) keskin kalır
    ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
    if ic and ic.name.startswith("AGAC") and float(kiyi_d(ob.location.x, ob.location.y)) < HOLDOUT_M:
        ob.is_holdout = True
s = sc2
s.render.film_transparent = True
s.cycles.samples = 16
s.cycles.use_denoising = False
s.cycles.use_adaptive_sampling = False
s.view_settings.view_transform = 'Standard'
s.view_settings.look = 'None'
s.view_settings.exposure = 0.0
s.render.resolution_x, s.render.resolution_y = COZ
s.render.image_settings.color_mode = 'RGBA'
sahil_v, kiyi_v = ns["_sahil_v"], ns["kiyi_v"]
W, H = COZ
for ad, k in KAM.items():
    blok.location.z = k["kalk"]
    s.camera = kams[ad]
    s.render.filepath = os.path.join(OUT, ad + "_maske.png")
    bpy.ops.render.render(write_still=True, scene=s.name)
    hat = []
    for i in range(-160, 241):               # kıyı yolunun 35 m deniz tarafı: hiç yumuşatılmaz
        u = i * 2.5
        sv = sahil_v(u)
        if KIYI_PAY is not None:               # yalnız su kenarı + KIYI_PAY m (kumsal) korunur
            v = float(kiyi_v(u)) + KIYI_PAY
        else:
            v = (sv + 35.0) if sv is not None else float(kiyi_v(u)) + 55.0
        p = world_to_camera_view(s, s.camera, Vector((u, v, 0.0)))
        if p.z > 0:
            hat.append((p.x * W, (1.0 - p.y) * H))
    json.dump(hat, open(os.path.join(OUT, ad + "_kiyi.json"), "w"))
    print("maske", ad, flush=True)
blok.location.z = 0.0
