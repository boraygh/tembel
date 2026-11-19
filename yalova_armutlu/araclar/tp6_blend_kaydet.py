# T_P-6 sahnesini açılıp düzenlenebilir .blend olarak kaydeder: dokular dosyaya gömülü, kameralar hazır
# (CAM_TP6_KOSE: sunumdaki köşe açısı, CAM_TP6_ORTADAN, CAM_TP6_UST: tepeden ortografik plan görünüşü).
# Kullanım: blender -b --factory-startup -P tp6_blend_kaydet.py -- CIKTI.blend
import sys, os, runpy, gc, math
import bpy
from mathutils import Vector
BURASI = os.path.dirname(os.path.abspath(__file__))
cikti = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
sys.path.insert(0, os.path.join(BURASI, ".."))
import tp6_plan

sys.argv = [sys.argv[0], "--"]
ns = runpy.run_path(os.path.join(BURASI, "..", "yalova_armutlu_16blok.py"), run_name="tp6")
tp6_plan.uygula(ns)
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
coll = bpy.data.collections["KAMERA_ISIK"]
t = bpy.data.objects["TEKNELER"]                     # tp6_onizleme.py ile aynı: yat kadraj altında kalmasın
for v in t.data.vertices:
    if (v.co.x - 112.0) ** 2 + (v.co.y + 106.0) ** 2 < 81.0:
        v.co.x -= 7.8
        v.co.y += 9.1

T0 = Vector((22.4, -46.0, 0.0))
YON = Vector((138.0 - 22.4, -221.0 + 46.0, 0.0)).normalized()
D3 = (Vector((138.0, -221.0, 70.0)) - T0).length
K2 = T0 + YON * D3 * math.cos(math.radians(28.0)) + Vector((0, 0, D3 * math.sin(math.radians(28.0))))
kose = ns["kamera"]("CAM_TP6_KOSE", tuple(K2), (22.4, -46.0, 0.0), 42.0, coll)
ns["kamera"]("CAM_TP6_ORTADAN", (-1.0, -199.0, 147.0), (-1.0, -24.0, 0.0), 35.0, coll)
cd = bpy.data.cameras.new("CAM_TP6_UST")
cd.type = 'ORTHO'
cd.ortho_scale = 175.0
cd.clip_start, cd.clip_end = 1.0, 2000.0
ust = bpy.data.objects.new("CAM_TP6_UST", cd)
ust.location = (-1.0, -4.0, 400.0)
coll.objects.link(ust)

sc.camera = kose
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.cycles.samples = 128
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=cikti, compress=True)
print("kaydedildi:", cikti, f"{os.path.getsize(cikti) / 1e6:.1f} MB", flush=True)
