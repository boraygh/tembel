# Yaya hizası (göz yüksekliği 1.65 m) kareleri: 2 nokta perspektif (yatay kamera + dikey kaydırma).
# Kullanım: blender -b --factory-startup -P yaya_hizasi.py -- --onizle            (tüm adaylar, düşük çözünürlük)
#           blender -b --factory-startup -P yaya_hizasi.py -- --sec Y1 [--ornek N] (final render)
#           blender -b --factory-startup -P yaya_hizasi.py -- --sec Y1 --maske     (yumuşatma maskesi)
# Maske sonrası girdi: ../video/araclar/girdi_yap.py, filigran: ../video/araclar/filigran.py
import sys, os, runpy, gc, math
import bpy
from mathutils import Vector
OUT = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONIZLE, MASKE = "--onizle" in arg, "--maske" in arg
SEC = arg[arg.index("--sec") + 1] if "--sec" in arg else None
ORNEK = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 256
GOZ = 1.65
ADAY = {   # ad: (kamera xy, bakış noktası xy, lens, dikey kaydırma)
    "Y1": ((54.0, -90.0), (20.0, -52.0), 24.0, 0.11),     # sahil parkından, palmiyeler arasından ön blok
    "Y2": ((52.0, -72.5), (18.0, -54.0), 24.0, 0.13),     # sahil yolunun kaldırımından ön blok, köşeden
    "Y3": ((1.5, -92.0), (4.0, -30.0), 24.0, 0.12),       # iki parsel arasındaki yolun başından, bloklar dizisi
    "Y1b": ((50.0, -85.0), (19.0, -54.0), 24.0, 0.12),    # Y1'den yakın, sahil yolu kenarındaki parktan
    "Y1c": ((47.0, -82.0), (18.0, -55.0), 22.0, 0.13),    # daha yakın, daha geniş açı
}
TEMIZ = {"Y1b": 11.0, "Y1c": 11.0}                        # kameranın bu yarıçapındaki ağaçlar gizlenir (m)
sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(OUT, "..", "yalova_armutlu_16blok.py"), run_name="yaya")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
coll = bpy.data.collections["KAMERA_ISIK"]


def kamera(ad):
    (cx, cy), (tx, ty), lens, kay = ADAY[ad]
    cam = ns["kamera"]("YAYA_" + ad, (cx, cy, GOZ), (tx, ty, GOZ), lens, coll)
    cam.data.shift_y = kay
    cam.data.clip_start = 0.1
    # kameranın 7 m yakınındaki ağaçlar kadrajı kapatmasın
    for ob in bpy.data.objects:
        ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
        if ic and ic.name.startswith("AGAC") and (ob.location.xy - Vector((cx, cy))).length < TEMIZ.get(ad, 7.0):
            ob.hide_render = True
    return cam


if ONIZLE:
    for ad in (arg[arg.index("--sadece") + 1].split(",") if "--sadece" in arg else ADAY):
        for ob in bpy.data.objects:
            if ob.instance_type == 'COLLECTION' and ob.hide_render:
                ob.hide_render = False
        sc2.camera = kamera(ad)
        sc2.render.resolution_x, sc2.render.resolution_y = 960, 540
        sc2.cycles.samples = 16
        sc2.render.filepath = os.path.join(OUT, f"oniz_{ad}.png")
        bpy.ops.render.render(write_still=True, scene=sc2.name)
        print("önizleme", ad, flush=True)
    sys.exit(0)

sc2.camera = kamera(SEC)
sc2.render.resolution_x, sc2.render.resolution_y = 2560, 1440
if not MASKE:
    sc2.cycles.samples = ORNEK
    sc2.render.filepath = os.path.join(OUT, f"{SEC}_render.png")
    bpy.ops.render.render(write_still=True, scene=sc2.name)
    print("render tamam", flush=True)
    sys.exit(0)

# ---- maske: proje mimarisi siyah (keskin), geri kalan her şey beyaz (yapay zekâ gerçek fotoğrafa çevirir) ----
MIMARI = {"Traverten", "Beyaz_Kompozit", "Kat_Silmesi", "Antrasit", "Bazalt_Kaide", "Sampanya_Bronz", "Ahsap_Tik",
          "Cephe_Cami", "Cam_Korkuluk", "Tas_Kaplama", "Minder", "Cati_Cakil", "Perde", "Ic_Siva", "Ic_Duvar",
          "Ic_Tavan", "Ic_Parke", "Doseme_Kumas", "Hali", "Tablo", "Nevresim", "Mobilya_Ahsap", "Lake_Mutfak",
          "Mobilya_Koyu", "Lamba"}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    outs = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
    if not outs:
        continue
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[1].default_value = 1.0
    v = 0.0 if m.name.split(".")[0] in MIMARI else 1.0
    em.inputs[0].default_value = (v, v, v, 1.0)
    for o in outs:
        for l in list(o.inputs["Surface"].links):
            nt.links.remove(l)
        nt.links.new(em.outputs[0], o.inputs["Surface"])
s = sc2
s.render.film_transparent = True
s.cycles.samples = 16
s.cycles.use_denoising = False
s.cycles.use_adaptive_sampling = False
s.view_settings.view_transform = 'Standard'
s.view_settings.look = 'None'
s.view_settings.exposure = 0.0
s.render.image_settings.color_mode = 'RGBA'
s.render.filepath = os.path.join(OUT, f"{SEC}_maske.png")
bpy.ops.render.render(write_still=True, scene=s.name)
print("maske tamam", flush=True)
