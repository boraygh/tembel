# Etüt klip girdileri (8 + 7 v3 parca_v3.py / parca_zincir.py ile aynı işlem, kareler bu videonun kareler_hq'sundan):
#   python3 parca.py duz K çıktı.mp4      -> klip K (1'den): kareler_hq -> on_duzelt -> 1920x1080 Lanczos, CRF 16
#   python3 parca.py zincir K ONCEKI.mp4 çıktı.mp4
#       klip K, başı klip K-1'in bitmiş (Kling) kareleriyle: GECIS + GECIS_UZ'a kadar komşu, ZINCIR_HARMAN karede
#       Blender'a harman; Blender karelerinin rengi bağ noktasında komşuya eşlenir ve SONUM karede söner (ani bir
#       parlaklık düşüşünü Kling ışık değişimi sanıp çıktıya taşıyabilir).
# Kareler: KARELER ortam değişkeni ya da video_etut/kareler_hq.
import os, subprocess, sys
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
sys.path.append(os.path.join(D, "..", "..", "..", "video_8_7", "araclar", "v3"))   # yalnız on_duzelt; plan buradaki
import on_duzelt
import plan
KL = os.environ.get("KARELER", os.path.join(D, "..", "..", "kareler_hq"))
W, H = 1920, 1080
SONUM = 96


def bl(i):
    return on_duzelt.duzelt(np.asarray(Image.open(os.path.join(KL, f"k_{i:04d}.jpg")).convert("RGB").resize((W, H), Image.LANCZOS)))


def kodla(cikti):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24",
                             "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                             "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)


mod, k = sys.argv[1], int(sys.argv[2])
ilk, son = plan.KLIP[k - 1]
eksik = [i for i in range(ilk, son) if not os.path.exists(os.path.join(KL, f"k_{i:04d}.jpg"))]
if eksik:
    sys.exit(f"eksik kare: {len(eksik)} (ilk {eksik[:5]})")
if mod == "duz":
    cikti = sys.argv[3]
    enc = kodla(cikti)
    for i in range(ilk, son):
        enc.stdin.write(np.clip(bl(i) + 0.5, 0, 255).astype(np.uint8).tobytes())
else:
    komsu, cikti = sys.argv[3], sys.argv[4]
    kbas = plan.KLIP[k - 2][0]
    bag, harman = plan.GECIS[k - 2] + plan.GECIS_UZ, plan.ZINCIR_HARMAN
    assert ilk == plan.GECIS[k - 2] and bag + harman <= plan.KLIP[k - 2][1]
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", komsu, "-vf", f"scale={W}:{H},select='between(n\\,{ilk - kbas}\\,{bag + harman - kbas - 1})'",
                        "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    K = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    assert len(K) == bag + harman - ilk, len(K)
    A = K[max(0, bag - 8 - ilk):].reshape(-1, 3).astype(np.float32)
    B = np.concatenate([bl(i).reshape(-1, 3) for i in range(max(ilk, bag - 8), bag + harman)])
    g = B.std(0)
    g = A.std(0) / np.maximum(g, 1e-3)
    o = A.mean(0) - B.mean(0) * g
    print("renk eşleme: kazanç", g.round(3), "ofset", o.round(1))
    enc = kodla(cikti)
    for i in range(ilk, son):
        if i < bag:
            f = K[i - ilk].astype(np.float32)
        else:
            f = bl(i)
            e = max(0.0, 1.0 - (i - bag) / SONUM)
            f = f + e * (f * g + o - f)
            if i < bag + harman:
                w = (i - bag + 1) / (harman + 1)
                f = K[i - ilk].astype(np.float32) * (1 - w) + f * w
        enc.stdin.write(np.clip(f + 0.5, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close()
enc.wait()
print(cikti, f"{(son - ilk) / 24:.2f} sn")
