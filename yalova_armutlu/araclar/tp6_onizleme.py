# T_P-6 vaziyet planına göre kredisiz Blender önizlemesi: köşe (K2, sunumdaki açı), ortadan (O1) ve plan
# kontrolü için tepeden ortografik görünüş (UST). Mimari 16blok.py'deki gibi; bloklar tp6_plan.py'den.
# Kullanım: blender -b --factory-startup -P tp6_onizleme.py -- --klasor DIR [--sadece K2,O1,UST] [--ornek N]
import sys, os, runpy, gc, math
import bpy
from mathutils import Vector
BURASI = os.path.dirname(os.path.abspath(__file__))
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = arg[arg.index("--klasor") + 1] if "--klasor" in arg else BURASI
ORNEK = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 64
SADECE = arg[arg.index("--sadece") + 1].split(",") if "--sadece" in arg else ["K2", "O1", "UST"]
sys.path.insert(0, os.path.join(BURASI, ".."))
import tp6_plan

# ortadan_kose_6x7.py ile aynı kameralar
T0 = Vector((22.4, -46.0, 0.0))
YON = Vector((138.0 - 22.4, -221.0 + 46.0, 0.0)).normalized()
D3 = (Vector((138.0, -221.0, 70.0)) - T0).length
K2 = T0 + YON * D3 * math.cos(math.radians(28.0)) + Vector((0, 0, D3 * math.sin(math.radians(28.0))))
KAMERA = {"K2": (tuple(K2), (22.4, -46.0, 0.0), 42.0, (1920, 1080)),
          "O1": ((-1.0, -199.0, 147.0), (-1.0, -24.0, 0.0), 35.0, (1920, 1080))}

sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(BURASI, "..", "yalova_armutlu_16blok.py"), run_name="tp6")
tp6_plan.uygula(ns)
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
coll = bpy.data.collections["KAMERA_ISIK"]
t = bpy.data.objects["TEKNELER"]                     # ortadan_kose_6x7.py: yat kadraj altında kalmasın
for v in t.data.vertices:
    if (v.co.x - 112.0) ** 2 + (v.co.y + 106.0) ** 2 < 81.0:
        v.co.x -= 7.8
        v.co.y += 9.1

for ad in SADECE:
    if ad == "UST":
        cd = bpy.data.cameras.new("TP6_UST")
        cd.type = 'ORTHO'
        cd.ortho_scale = 175.0
        cd.clip_start, cd.clip_end = 1.0, 2000.0
        cam = bpy.data.objects.new("TP6_UST", cd)
        cam.location = (-1.0, -4.0, 400.0)
        coll.objects.link(cam)
        coz = (1400, 2000)
    else:
        c, h, L, coz = KAMERA[ad]
        cam = ns["kamera"]("TP6_" + ad, c, h, L, coll)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = coz
    sc.cycles.samples = ORNEK if ad != "UST" else max(16, ORNEK // 2)
    sc.render.filepath = os.path.join(OUT, f"tp6_{ad}.png")
    bpy.ops.render.render(write_still=True, scene=sc.name)
    print("önizleme", ad, flush=True)
