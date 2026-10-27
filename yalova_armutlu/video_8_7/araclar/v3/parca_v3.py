# v3 klip girdisi: kareler_hq[a:b] -> on_duzelt (girişin tonu) -> 1920x1080 Lanczos, CRF 16.
# Kullanım: python3 parca_v3.py İLK SON çıktı.mp4
import os, subprocess, sys
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import on_duzelt
a, b, cikti = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
KL = os.path.join(D, "..", "kareler_hq")
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "24",
                        "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
for i in range(a, b):
    f = Image.open(os.path.join(KL, f"k_{i:04d}.jpg")).convert("RGB").resize((1920, 1080), Image.LANCZOS)
    enc.stdin.write(np.clip(on_duzelt.duzelt(np.asarray(f)) + 0.5, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close()
enc.wait()
print(cikti, f"{(b - a) / 24:.2f} sn")
