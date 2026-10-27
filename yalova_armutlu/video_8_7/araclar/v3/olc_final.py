# Tam videoda kare başına parlaklık ve netlik; geçiş pencerelerinde ve genelde en büyük sıçramalar.
import subprocess, sys
import numpy as np
sys.path.insert(0, "v3")
import plan
w, h = 480, 270
p = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                    "-pix_fmt", "rgb24", "-"], capture_output=True)
v = np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3).astype(np.float32)
n = min(len(v), plan.SON)
# alt-sağdaki mini plan ve üstteki etiketler hariç: orta bant
orta = v[:n, 60:200, :330]
par = orta.mean((1, 2, 3))
gri = orta.mean(3)
net = np.abs(np.diff(gri, axis=2)).mean((1, 2))
print("kare", len(v), "görüntü", n)
for g in plan.GECIS:
    a, b = g - 24, g + plan.GECIS_UZ + 24
    print(f"geçiş {g}: parlaklık {par[a]:.1f} -> {par[b]:.1f}  en büyük kare farkı {np.abs(np.diff(par[a:b])).max():.2f}  "
          f"netlik {net[a]:.2f} -> {net[b]:.2f}  en büyük {np.abs(np.diff(net[a:b])).max():.2f}")
d = np.abs(np.diff(par))
i = np.argsort(d)[-5:][::-1]
print("genel en büyük parlaklık sıçramaları:", [(int(k), round(float(d[k]), 2)) for k in i])
dn = np.abs(np.diff(net))
i = np.argsort(dn)[-5:][::-1]
print("genel en büyük netlik sıçramaları:", [(int(k), round(float(dn[k]), 2)) for k in i])
# 1 sn'lik kayan ortalamaya göre netlik dalgalanması (karıncalanma/pompalama göstergesi)
k = np.convolve(net, np.ones(24) / 24, mode="same")
print("netlik dalgalanması (std, 1 sn ortalamaya göre):", round(float((net - k)[12:-12].std()), 3))
