# Zincirleme klip girdisi: başta komşu klibin bitmiş (Kling) kareleri, kısa bir harmanla tonlanmış Blender karelerine geçer.
# Kling gerçekçi kareleri neredeyse aynen koruduğu için yeni klip komşusunun görünümünden devam eder.
# Kullanım: python3 parca_zincir.py KOMSU.mp4 KOMSU_BAS İLK BAĞ HARMAN SON çıktı.mp4
#   İLK..BAĞ: komşu klipten, BAĞ..BAĞ+HARMAN: komşudan Blender'a harman, sonrası Blender (kare numaraları rota karesi)
# Blender karelerinin rengi bağ noktasında komşuya eşlenir (kanal başına kazanç/ofset) ve eşleme SONUM karede söner:
# girdide ani bir parlaklık düşüşü olursa Kling onu ışık değişimi sanıp çıktıya taşıyabilir.
import os, subprocess, sys
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import on_duzelt
komsu, kbas, ilk, bag, harman, son, cikti = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
KL = os.path.join(D, "..", "kareler_hq")
W, H = 1920, 1080
SONUM = 96
p = subprocess.run(["ffmpeg", "-v", "error", "-i", komsu, "-vf", f"select='between(n\\,{ilk - kbas}\\,{bag + harman - kbas - 1})'",
                    "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
K = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
assert len(K) == bag + harman - ilk, len(K)


def bl(i):
    return on_duzelt.duzelt(np.asarray(Image.open(os.path.join(KL, f"k_{i:04d}.jpg")).convert("RGB").resize((W, H), Image.LANCZOS)))


A = K[max(0, bag - 8 - ilk):].reshape(-1, 3).astype(np.float32)
B = np.concatenate([bl(i).reshape(-1, 3) for i in range(max(ilk, bag - 8), bag + harman)])
g = A.std(0) / B.std(0)
o = A.mean(0) - B.mean(0) * g
print("renk eşleme: kazanç", g.round(3), "ofset", o.round(1))
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24",
                        "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
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
