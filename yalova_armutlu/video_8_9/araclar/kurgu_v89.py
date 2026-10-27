# 8+9 deniz manzarası videosunu birleştirir. Önceki kurgu.py'nin hız eğrisi / geçiş mantığını kullanır,
# üstüne segment başına dijital yaklaşma ve kaplama (mini plan + etiket, açılış başlığı) ekler.
# Kullanım: python3 kurgu_v89.py PLAN.json CIKTI.mp4 [CRF]
#
# Plan öğesi (kurgu.py'dekilere ek olarak):
#   "zoom": [z0, z1], "merkez": [cx, cy]      -> segment boyunca z0'dan z1'e yumuşak yaklaşma (0-1 merkez)
#   "kaplama": png, "k_bas": sn, "k_son": sn, "k_gir": sn, "k_cik": sn
#       -> RGBA kaplama segmentin k_bas..k_son aralığında, k_gir/k_cik sürelerinde belirip kaybolur
#   "karart_cik": sn                          -> segment sonunda siyaha iniş
import json, os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "video", "araclar"))
import kurgu as K

W, H, FPS = K.W, K.H, K.FPS
_kap = {}


def kaplama(yol):
    if yol not in _kap:
        a = np.asarray(Image.open(yol).convert("RGBA").resize((W, H), Image.LANCZOS), np.float32)
        _kap[yol] = (a[..., :3], a[..., 3:] / 255.0)
    return _kap[yol]


def yakinlas(k, z, cx, cy):
    if z <= 1.0001:
        return k
    w, h = W / z, H / z
    x0 = min(max(cx * W - w / 2, 0), W - w)
    y0 = min(max(cy * H - h / 2, 0), H - h)
    im = Image.fromarray(k).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
    return np.asarray(im)


def isle(s, kareler):
    n = len(kareler)
    z0, z1 = s.get("zoom", [1.0, 1.0])
    cx, cy = s.get("merkez", [0.5, 0.5])
    kap = kaplama(s["kaplama"]) if s.get("kaplama") else None
    out = []
    for i, k in enumerate(kareler):
        p = i / max(n - 1, 1)
        k = yakinlas(k, z0 + (z1 - z0) * K.yumusak(p), cx, cy)
        if kap is not None:
            t = i / FPS
            bas, son = s.get("k_bas", 0.0), s.get("k_son", n / FPS)
            a = 0.0
            if bas <= t <= son:
                a = 1.0
                if s.get("k_gir"):
                    a = min(a, K.yumusak((t - bas) / s["k_gir"]))
                if s.get("k_cik"):
                    a = min(a, K.yumusak((son - t) / s["k_cik"]))
            if a > 0:
                rgb, al = kap
                al = al * a
                k = K.u8(k.astype(np.float32) * (1 - al) + rgb * al)
        if s.get("karart_cik"):
            m = s["karart_cik"] * FPS
            if i >= n - m:
                k = K.u8(k.astype(np.float32) * K.yumusak((n - 1 - i) / m))
        out.append(np.ascontiguousarray(k))
    return out


def main(plan_yol, cikti, crf=20):
    plan = json.load(open(plan_yol))
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-tune", "film",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
    kuyruk, n = [], 0

    def yaz(kareler):
        nonlocal n
        for k in kareler:
            enc.stdin.write(k.tobytes())
            n += 1

    for s in plan:
        tur = s.get("tur", "klip")
        if tur == "bekle":
            yeni = [kuyruk[-1]] * int(round(s["sure"] * FPS))
        elif tur == "kapanis":
            yeni = list(K.oku(s["klip"]))
        else:
            yeni = isle(s, K.segment_kareleri(s))
        G = int(s.get("gecis", 0))
        if kuyruk and tur != "bekle" and G > 0:
            G = min(G, len(kuyruk), len(yeni))
            kuyruk, kuyruk_son = kuyruk[:-G], kuyruk[-G:]
            for i in range(G):
                w = K.yumusak((i + 1) / (G + 1))
                yeni[i] = K.u8(kuyruk_son[i].astype(np.float32) * (1 - w) + yeni[i].astype(np.float32) * w)
        if s.get("karart_gir"):
            m = s["karart_gir"] * FPS
            yeni = [K.u8(k.astype(np.float32) * K.yumusak(i / m)) if i < m else k for i, k in enumerate(yeni)]
        yaz(kuyruk)
        kuyruk = yeni
        print(f"{s.get('ad', tur)}: {len(yeni)} kare ({len(yeni) / FPS:.2f} sn), geçiş {G} kare", flush=True)
    yaz(kuyruk)
    enc.stdin.close()
    enc.wait()
    print(cikti, f"{n / FPS:.2f} sn")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 20)
