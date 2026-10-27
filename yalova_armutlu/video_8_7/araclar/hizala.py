# Kling çıktısının girdiye göre kare kaymasını bulur: birkaç örnek karede -4..+4 kaymada kenar korelasyonu.
# Kullanım: python3 hizala.py GIRDI.mp4 CIKTI.mp4
import sys
import numpy as np
sys.argv, (gir, cik) = sys.argv[:1], sys.argv[1:3]
import importlib.util
from vv_kontrol_ortak import kareler, kenar
a, b = kareler(gir), kareler(cik)
print(f"girdi {len(a)}  çıktı {len(b)}")
orn = list(range(12, min(len(a), len(b)) - 12, max(1, (min(len(a), len(b)) - 24) // 10)))
for s in range(-4, 5):
    k = [np.corrcoef(kenar(a[i]).ravel(), kenar(b[i + s]).ravel())[0, 1] for i in orn if 0 <= i + s < len(b)]
    print(f"kayma {s:+d}: {np.mean(k):.3f}")
