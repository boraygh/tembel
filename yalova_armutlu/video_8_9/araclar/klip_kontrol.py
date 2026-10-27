# Kling klibini denetler: kamera sabit mi (ilk kareye göre faz korelasyonu kayması ve ölçek),
# başlangıç karesine benzerlik, ve 4 karelik pafta (AD_pafta.jpg).
# Kullanım: python3 klip_kontrol.py AD KLIP.mp4 [BASLANGIC.png]
import subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540


def kareler(yol):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", yol, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)


def gri(a):
    return a.astype(np.float32).mean(2)


def kayma(a, b):
    """b'nin a'ya göre (dx, dy) kayması, faz korelasyonu."""
    A, B = np.fft.fft2(a - a.mean()), np.fft.fft2(b - b.mean())
    R = A * np.conj(B); R /= np.abs(R) + 1e-6
    r = np.real(np.fft.ifft2(R))
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    dy = iy if iy < a.shape[0] / 2 else iy - a.shape[0]
    dx = ix if ix < a.shape[1] / 2 else ix - a.shape[1]
    return dx, dy, r.max()


ad, yol = sys.argv[1], sys.argv[2]
k = kareler(yol)
n = len(k)
fps = 24
print(f"{ad}: {n} kare ({n / fps:.2f} sn)")
g0 = gri(k[0])
# bölgeler: tüm kare, sol şerit (komşu blok), alt şerit (korkuluk)
bolge = {"tum": (slice(0, H), slice(0, W)), "sol": (slice(0, H), slice(0, int(W * 0.2))),
         "alt": (slice(int(H * 0.75), H), slice(0, W))}
for i in (n // 4, n // 2, 3 * n // 4, n - 1):
    gi = gri(k[i])
    s = "  ".join(f"{b}: {kayma(g0[sl], gi[sl])[:2]}" for b, sl in bolge.items())
    fark = np.abs(g0 - gi).mean()
    print(f"  kare {i:3d} ({i / fps:4.2f} sn)  kayma {s}  ort. fark {fark:5.1f}")
if len(sys.argv) > 3:
    b = np.asarray(Image.open(sys.argv[3]).convert("RGB").resize((W, H), Image.LANCZOS))
    print("  başlangıç karesine ort. fark:", round(float(np.abs(gri(b) - g0).mean()), 1))
f = ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 22)
sec = [0, n // 3, 2 * n // 3, n - 1]
c = Image.new("RGB", (2 * W + 8, 2 * H + 8))
for j, i in enumerate(sec):
    im = Image.fromarray(k[i])
    ImageDraw.Draw(im).text((8, 6), f"{ad} {i / fps:.2f} sn", font=f, fill="white", stroke_width=3, stroke_fill="black")
    c.paste(im, ((j % 2) * (W + 8), (j // 2) * (H + 8)))
c.save(f"{ad}_pafta.jpg", quality=84)
