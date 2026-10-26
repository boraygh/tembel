# NB çıktısı ile Blender karesini karşılaştırır: yan yana pafta + 4x4 karo kenar korelasyonu.
# Düşük korelasyonlu karo = kompozisyon değişmiş olabilir. Kullanım: python3 dogrula.py K3
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def kenar(im, W=960, H=540):
    g = np.asarray(im.convert("L").resize((W, H), Image.LANCZOS), np.float32)
    e = np.abs(np.diff(g, axis=1, prepend=g[:, :1])) + np.abs(np.diff(g, axis=0, prepend=g[:1]))
    return np.asarray(Image.fromarray(np.clip(e * 3, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32)

ad = sys.argv[1]
b = Image.open(ad + "_render.png").convert("RGB")
n = Image.open(ad + "_nb.png").convert("RGB")
eb, en = kenar(b), kenar(n)
H, W = eb.shape
tablo = np.zeros((4, 4))
for i in range(4):
    for j in range(4):
        x = eb[i * H // 4:(i + 1) * H // 4, j * W // 4:(j + 1) * W // 4].ravel()
        y = en[i * H // 4:(i + 1) * H // 4, j * W // 4:(j + 1) * W // 4].ravel()
        tablo[i, j] = np.corrcoef(x, y)[0, 1]
print(ad, "karo korelasyonları (satır üstten):")
for r in tablo:
    print("  " + "  ".join(f"{v:5.2f}" for v in r))
print(f"  en düşük {tablo.min():.2f}  ortalama {tablo.mean():.2f}")
P = Image.new("RGB", (1290, 360), (255, 255, 255))
P.paste(b.resize((640, 360), Image.LANCZOS), (0, 0)); P.paste(n.resize((640, 360), Image.LANCZOS), (650, 0))
P.save(ad + "_dogrula.jpg", quality=88)
