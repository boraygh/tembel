# ERDEM İNŞAAT kapanış kartı (1920x1080, 24 fps): E işareti parça parça çizilir, yazılar belirir,
# altında "YALOVA · ARMUTLU". Kullanım: python3 kapanis.py CIKTI.mp4 [süre_sn]
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from filigran import BEYAZ, TURUNCU, YAZI_KALIN, YAZI_ORTA, _font, _yaz

W, H, FPS = 1920, 1080, 24
SURE = float(sys.argv[2]) if len(sys.argv) > 2 else 4.5
GECIKME = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0   # animasyon başlangıcı (sn)
ZEMIN = np.array((10, 13, 18), np.float32)          # #0A0D12
S, SS = 150, 4                                        # işaret yüksekliği (px), süper örnekleme
ALT_RENK = (201, 206, 214)


def katmanlar():
    """kilit() ile aynı ölçüler; her parça ayrı RGBA katman (tam kare boyutunda)."""
    N = S * SS
    u = N / 100.0
    f1, f2 = _font(YAZI_KALIN, 0.50 * N), _font(YAZI_ORTA, 0.235 * N)
    bosluk, t1 = 0.34 * N, 0.02 * N
    sol1 = f1.getbbox("E", anchor="ls")[0]
    sag1 = f1.getlength("ERDE") + 4 * t1 + f1.getbbox("M", anchor="ls")[2]
    sol2 = f2.getbbox("İ", anchor="ls")[0]
    sag2 = f2.getlength("İNŞAA") + f2.getbbox("T", anchor="ls")[2]
    aralik2 = max(0.0, ((sag1 - sol1) - (sag2 - sol2)) / 5)
    gen = N + bosluk + (sag1 - sol1)                  # kilidin mürekkep genişliği
    ox = (W * SS - gen) / 2                           # yatay ortala
    oy = (H * SS - N) / 2 - 0.10 * N                  # alt yazıya yer: biraz yukarı
    parcalar = {}

    def yeni():
        im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    for ad, kutu, renk in (("govde", (0, 0, 25, 100), BEYAZ), ("ust", (27, 0, 100, 21), BEYAZ),
                           ("alt", (27, 79, 100, 100), BEYAZ), ("bar", (27, 39.5, 78, 60.5), TURUNCU)):
        im, d = yeni()
        x0, y0, x1, y1 = kutu
        d.rectangle([ox + x0 * u, oy + y0 * u, ox + x1 * u - 1, oy + y1 * u - 1], fill=renk + (255,))
        parcalar[ad] = (im, (ox + x0 * u, oy + y0 * u, ox + x1 * u, oy + y1 * u))
    x0 = ox + N + bosluk
    im, d = yeni()
    _yaz(d, x0 - sol1, oy + 0.50 * N, "ERDEM", f1, BEYAZ + (255,), t1)
    parcalar["erdem"] = (im, (x0, oy, x0 + sag1 - sol1, oy + 0.5 * N))
    im, d = yeni()
    _yaz(d, x0 - sol2, oy + 1.00 * N, "İNŞAAT", f2, BEYAZ + (255,), aralik2)
    parcalar["insaat"] = (im, (x0, oy + 0.7 * N, x0 + sag1 - sol1, oy + N))
    # ayraç çizgi + alt yazı (kilidin altında, ortalı)
    cy = oy + N + 0.55 * N
    im, d = yeni()
    lw = 0.9 * N
    d.rectangle([W * SS / 2 - lw / 2, cy - 1.5 * SS / 2, W * SS / 2 + lw / 2, cy + 1.5 * SS / 2],
                fill=(255, 255, 255, 90))
    parcalar["cizgi"] = (im, (W * SS / 2 - lw / 2, cy - SS, W * SS / 2 + lw / 2, cy + SS))
    f3 = _font(YAZI_ORTA, 0.15 * N)
    metin, ar = "YALOVA  ·  ARMUTLU", 0.045 * N
    tw = f3.getlength(metin) + (len(metin) - 1) * ar
    im, d = yeni()
    _yaz(d, W * SS / 2 - tw / 2, cy + 0.36 * N, metin, f3, ALT_RENK + (255,), ar)
    parcalar["alt_yazi"] = (im, (W * SS / 2 - tw / 2, cy + 0.2 * N, W * SS / 2 + tw / 2, cy + 0.4 * N))
    out = {}
    for ad, (im, kutu) in parcalar.items():
        a = np.asarray(im.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255.0
        out[ad] = (a, tuple(v / SS for v in kutu))
    return out


def yumusak(t):                                       # easeOutCubic, 0-1 aralığına kırpılmış
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ac(t, t0, t1):
    return yumusak((t - t0) / (t1 - t0))


def silme_maskesi(kutu, oran, eksen):
    """Kutuyu soldan sağa (x) ya da aşağıdan yukarı (y) açan yumuşak kenarlı maske."""
    x0, y0, x1, y1 = kutu
    if eksen == "x":
        sinir = x0 + (x1 - x0) * oran
        xs = np.arange(W, dtype=np.float32)
        return np.clip((sinir - xs) / 2.0 + 0.5, 0, 1)[None, :]
    sinir = y1 - (y1 - y0) * oran
    ys = np.arange(H, dtype=np.float32)
    return np.clip((ys - sinir) / 2.0 + 0.5, 0, 1)[:, None]


def main(cikti):
    L = katmanlar()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.65)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    zemin = ZEMIN[None, None, :] * (1.18 - 0.28 * np.clip(r, 0, 1))[..., None]   # hafif merkez aydınlığı
    zemin = zemin + np.random.default_rng(7).normal(0.0, 1.1, (H, W, 1)).astype(np.float32)  # bantlaşmayı kır
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                          "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", cikti],
                         stdin=subprocess.PIPE)
    plan = [("govde", 0.15, 0.70, "y", 0), ("ust", 0.35, 0.85, "x", 0), ("alt", 0.45, 0.95, "x", 0),
            ("bar", 0.70, 1.20, "x", 0), ("erdem", 0.95, 1.65, "x", 14), ("insaat", 1.20, 1.85, "x", 14),
            ("cizgi", 1.85, 2.45, "c", 0), ("alt_yazi", 2.05, 2.75, "f", 10)]
    for i in range(int(round(SURE * FPS))):
        t = i / FPS - GECIKME
        img = zemin.copy()
        for ad, t0, t1, tur, kay in plan:
            a, kutu = L[ad]
            o = ac(t, t0, t1)
            if o <= 0:
                continue
            rgb, al = a[..., :3], a[..., 3:4]
            if tur in ("x", "y"):
                m = silme_maskesi(kutu, o, tur)
                al = al * (m[..., None] if m.ndim == 2 else m)
            elif tur == "c":                          # ortadan iki yana açılan çizgi
                x0, _, x1, _ = kutu
                cx, yar = (x0 + x1) / 2, (x1 - x0) / 2 * o
                xs = np.arange(W, dtype=np.float32)
                al = al * np.clip(yar - np.abs(xs - cx) + 0.5, 0, 1)[None, :, None]
            if kay and o < 1:                         # hafif kayarak yerine oturma
                dx = int(round(kay * (1 - o)))
                if tur == "f":
                    rgb = np.roll(rgb, dx, axis=0); al = np.roll(al, dx, axis=0)
                else:
                    rgb = np.roll(rgb, -dx, axis=1); al = np.roll(al, -dx, axis=1)
            if tur in ("x", "f") and ad in ("erdem", "insaat", "alt_yazi"):
                al = al * o
            img = img * (1 - al) + rgb * 255.0 * al
        p.stdin.write(np.clip(img + 0.5, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    print(cikti, "tamam")


if __name__ == "__main__":
    main(sys.argv[1])
