# Kredisiz önizleme videosunun Blender animasyonu (8 + 7, denizde temsili gemi, rota.py'deki kamera yolu).
# Kullanım:
#   blender -b --factory-startup -P onizleme_blender.py -- --test 8          # rotadan 8 örnek kare + süre ölçümü
#   blender -b --factory-startup -P onizleme_blender.py -- --aralik 0 1977   # kareleri kareler/ altına render et
#   seçenekler: --coz 960x540  --ornek 8
import sys, os, json, runpy, gc, math, time
import bpy
from mathutils import Vector
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = int(arg[arg.index("--test") + 1]) if "--test" in arg else 0
ARALIK = (int(arg[arg.index("--aralik") + 1]), int(arg[arg.index("--aralik") + 2])) if "--aralik" in arg else None
COZ = tuple(int(v) for v in arg[arg.index("--coz") + 1].split("x")) if "--coz" in arg else (960, 540)
ORNEK = int(arg[arg.index("--ornek") + 1]) if "--ornek" in arg else 8
KLASOR = arg[arg.index("--klasor") + 1] if "--klasor" in arg else "kareler"
sys.argv = [sys.argv[0], "--", "--sol", "8", "--sag", "7"]
ns = runpy.run_path("/home/user/tembel/yalova_armutlu/yalova_armutlu_16blok.py", run_name="onizleme")
gc.disable()
sc, sc2 = ns["kur"]()
gc.enable()
import gemi87
gemi87.gemi(gemi87.GEMI, bpy.data.collections["CEVRE_DENIZ"])
import rota

# kamera yolunu kesen küçük nesneleri kaldır: yürüyüş hattında araç/ağaç/direk, kayma hattında ağaç tepeleri
kayma_x = [rota.DURAK[0][0], rota.DURAK[-1][0]]
silinen = 0
for ob in list(bpy.data.objects):
    ic = ob.instance_collection if ob.instance_type == 'COLLECTION' else None
    if ic is None or ic.name.startswith("TIP_BLOK"):
        continue
    x, y = ob.location.x, ob.location.y
    yuru = abs(x - rota.YURU_X) < 2.4 and -100 < y < 70
    kay = ic.name.startswith("AGAC") and min(abs(x - kx) for kx in kayma_x) < 3.5 and -85 < y < 70
    if yuru or kay:
        bpy.data.objects.remove(ob, do_unlink=True)
        silinen += 1
print("yoldan kaldırılan nesne:", silinen, flush=True)
bpy.context.view_layer.update()

# yürüyüş hattında zemin yüksekliği
dg = bpy.context.evaluated_depsgraph_get()
ys, zs, adlar = [], [], {}
y = rota.YURU_Y0 + 2.0
while y > rota.YURU_Y1 - 4.0:
    ok, loc, nor, _, obj, _ = sc.ray_cast(dg, Vector((rota.YURU_X, y, 40.0)), Vector((0, 0, -1)))
    z = loc.z if ok else 0.3
    ys.append(round(y, 2)); zs.append(round(z, 3))
    if ok:
        adlar[obj.name.split(".")[0]] = adlar.get(obj.name.split(".")[0], 0) + 1
    y -= 1.0
# tek tük yüksek isabetleri (tabela, bordür üstü) medyanla bastır
zm = [sorted(zs[max(0, i - 3):i + 4])[len(zs[max(0, i - 3):i + 4]) // 2] for i in range(len(zs))]
json.dump({"y": ys, "z": zm}, open(os.path.join(OUT, "zemin.json"), "w"))
print("zemin isabetleri:", adlar, "z aralığı", min(zm), max(zm), flush=True)

KARE = rota.kareler()
cd = bpy.data.cameras.new("ONIZLEME")
cd.lens, cd.sensor_width, cd.clip_start, cd.clip_end = 24.0, 36.0, 0.05, 15000.0
kam = bpy.data.objects.new("ONIZLEME", cd)
bpy.data.collections["KAMERA_ISIK"].objects.link(kam)
sc.camera = kam


def poz(k):
    kam.location = (k["x"], k["y"], k["z"])
    kam.rotation_euler = (math.radians(90.0 + k["p"]), 0.0, math.radians(-k["h"]))


r = sc.render
r.resolution_x, r.resolution_y = COZ
r.use_persistent_data = True
cy = sc.cycles
cy.samples = ORNEK
cy.adaptive_threshold = 0.05
cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces = 6, 2, 2
cy.transmission_bounces, cy.transparent_max_bounces = 4, 8
r.image_settings.file_format = 'JPEG'
r.image_settings.quality = 92
os.makedirs(os.path.join(OUT, KLASOR), exist_ok=True)

if TEST:
    secim = [int(i * (len(KARE) - 1) / (TEST - 1)) for i in range(TEST)]
    for i in secim:
        poz(KARE[i])
        r.filepath = os.path.join(OUT, "test", f"t_{i:04d}.jpg")
        t = time.time()
        bpy.ops.render.render(write_still=True, scene=sc.name)
        print(f"test kare {i} ({KARE[i]['bolum']}, {i / rota.FPS:.1f} sn): {time.time() - t:.1f} s", flush=True)
    sys.exit(0)

a, b = ARALIK if ARALIK else (0, len(KARE) - 1)
ADIM = int(arg[arg.index("--adim") + 1]) if "--adim" in arg else 1
t0 = time.time()
for i in range(a, min(b, len(KARE) - 1) + 1, ADIM):
    yol = os.path.join(OUT, KLASOR, f"k_{i:04d}.jpg")
    if os.path.exists(yol):
        continue
    poz(KARE[i])
    r.filepath = yol
    bpy.ops.render.render(write_still=True, scene=sc.name)
    if i % 24 == 0:
        print(f"kare {i}/{len(KARE)}  geçen {time.time() - t0:.0f} s", flush=True)
print("render tamam", flush=True)
