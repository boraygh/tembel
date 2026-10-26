# Kahraman bloğun (7105-G) görünen silueti: diğer her şey holdout, alfa = görünen blok pikselleri.
import sys, os, runpy, gc, json
import bpy
OUT = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
KAREL = arg[0].split(",") if arg else ["K1", "K2"]
sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(OUT, "..", "..", "yalova_armutlu_16blok.py"), run_name="sil")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
KAM = json.load(open(os.path.join(OUT, "kameralar_b.json")))
blok = bpy.data.objects["BLOK_7105-G"]
for ob in bpy.data.objects:
    if ob.type != 'CAMERA' and ob.type != 'LIGHT':
        ob.is_holdout = ob is not blok
s = sc2
s.render.film_transparent = True
s.cycles.samples = 4
s.cycles.use_denoising = False
s.cycles.use_adaptive_sampling = False
s.render.resolution_x, s.render.resolution_y = 1920, 1080
s.render.image_settings.color_mode = 'RGBA'
coll = bpy.data.collections["KAMERA_ISIK"]
for ad in KAREL:
    k = KAM[ad]
    blok.location.z = k["kalk"]
    s.camera = ns["kamera"]("SIL_" + ad, k["konum"], k["hedef"], k["lens"], coll)
    s.render.filepath = os.path.join(OUT, ad + "_siluet.png")
    bpy.ops.render.render(write_still=True, scene=s.name)
    print("siluet", ad, flush=True)
blok.location.z = 0.0
