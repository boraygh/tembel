# NB Pro çıktısının Blender karesine göre ölçek/kayma tahmini (kenar haritalarıyla kaba arama).
import sys
import numpy as np
from PIL import Image, ImageFilter

def kenar(im, W, H):
    g = np.asarray(im.convert("L").resize((W, H), Image.LANCZOS), np.float32)
    gx = np.abs(np.diff(g, axis=1, prepend=g[:, :1])); gy = np.abs(np.diff(g, axis=0, prepend=g[:1]))
    e = gx + gy
    e = np.asarray(Image.fromarray(np.clip(e * 4, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), np.float32)
    return (e - e.mean()) / (e.std() + 1e-6)

def hiza(blender, nb, W=960):
    b = Image.open(blender); n = Image.open(nb)
    H = round(W * b.size[1] / b.size[0])
    eb = kenar(b, W, H)
    en_full = Image.open(nb)
    en_full = en_full.convert("RGB")
    best = None
    for s in np.linspace(0.97, 1.03, 13):          # nb'yi s ölçeğiyle büyüt/küçült, merkezden kırp
        for mode in ("ger", "kirp"):
            if mode == "ger":
                im = en_full.resize((W, H), Image.LANCZOS)          # tam esnetme
            else:
                w0, h0 = en_full.size; ar = W / H
                if w0 / h0 > ar:
                    nw = h0 * ar; im = en_full.crop(((w0 - nw) / 2, 0, (w0 + nw) / 2, h0)).resize((W, H), Image.LANCZOS)
                else:
                    nh = w0 / ar; im = en_full.crop((0, (h0 - nh) / 2, w0, (h0 + nh) / 2)).resize((W, H), Image.LANCZOS)
            if abs(s - 1) > 1e-6:
                ww, hh = round(W * s), round(H * s)
                im2 = im.resize((ww, hh), Image.LANCZOS)
                l, t = (ww - W) // 2, (hh - H) // 2
                if s > 1:
                    im = im2.crop((l, t, l + W, t + H))
                else:
                    c = Image.new("RGB", (W, H)); c.paste(im2, (-l, -t)); im = c
            en = kenar(im, W, H)
            F = np.fft.fft2(eb) * np.conj(np.fft.fft2(en))
            r = np.real(np.fft.ifft2(F / (np.abs(F) + 1e-6)))
            iy, ix = np.unravel_index(np.argmax(r), r.shape)
            dy = iy if iy < H / 2 else iy - H; dx = ix if ix < W / 2 else ix - W
            sk = r.max()
            if best is None or sk > best[0]:
                best = (sk, mode, round(s, 3), dx, dy)
    return best

if __name__ == "__main__":
    print(hiza(sys.argv[1], sys.argv[2]))
