# Videoyu birleştirir: hız eğrileri (yumuşak giriş/çıkış), ters oynatma, klip birleşimlerinde
# kısa çapraz geçiş, siyahtan açılış, dondurma ve kapanış kartı.
# Zaman yeniden örneklenirken komşu iki kare doğrusal harmanlanır.
# Kullanım: python3 kurgu.py PLAN.json CIKTI.mp4 [CRF]
#
# Plan öğeleri:
#   {"klip": yol, "t0": sn, "t1": sn, "v": hız, "v0"/"v1": giriş/çıkış hızı, "a"/"b": rampa payı (0-1),
#    "gecis": önceki segmentle çapraz geçiş (kare), "karart_gir": siyahtan açılış (sn)}
#   {"tur": "bekle", "sure": sn}                         -> son kareyi dondur
#   {"tur": "kapanis", "klip": yol, "gecis": kare}       -> kapanış kartı
import json, subprocess, sys
import numpy as np

W, H, FPS = 1920, 1080, 24
_onbellek = {}


def oku(yol):
    if yol not in _onbellek:
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", yol, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        _onbellek[yol] = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    return _onbellek[yol]


def u8(k):
    return np.clip(k + 0.5, 0, 255).astype(np.uint8)


def kare(a, t):
    f = min(max(t * FPS, 0.0), len(a) - 1.0)
    i = int(np.floor(f)); w = f - i
    j = min(i + 1, len(a) - 1)
    if w < 0.02 or i == j:
        return a[i]
    if w > 0.98:
        return a[j]
    return u8(a[i].astype(np.float32) * (1 - w) + a[j].astype(np.float32) * w)


def yumusak(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def hiz(p, s):
    """İlerleme p (0-1) için hız: giriş rampası (a), sabit (v), çıkış rampası (b)."""
    v0, v, v1, a, b = s.get("v0", s["v"]), s["v"], s.get("v1", s["v"]), s.get("a", 0.0), s.get("b", 0.0)
    if a > 0 and p < a:
        return v0 + (v - v0) * yumusak(p / a)
    if b > 0 and p > 1 - b:
        return v + (v1 - v) * yumusak((p - (1 - b)) / b)
    return v


def segment_kareleri(s):
    a = oku(s["klip"])
    t0, t1 = s["t0"], s["t1"]
    yon = 1.0 if t1 >= t0 else -1.0
    L = abs(t1 - t0)
    t, out, son = t0, [], t0
    while (t - t1) * yon <= 1e-6:
        out.append(kare(a, t))
        son = t
        t += yon * max(hiz(abs(t - t0) / L, s), 0.05) / FPS
    if abs(son - t1) > 0.5 / FPS:
        out.append(kare(a, t1))                # son kareye tam otur (eşleşen anahtar kare)
    return out


def main(plan_yol, cikti, crf=22):
    plan = json.load(open(plan_yol))
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-tune", "film",
                            "-pix_fmt", "yuv420p", "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
    kuyruk, n = [], 0                          # henüz yazılmamış son kareler (geçiş için tutulur)

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
            yeni = list(oku(s["klip"]))
        else:
            yeni = segment_kareleri(s)
        G = int(s.get("gecis", 0))
        if kuyruk and tur != "bekle":
            if G > 0:
                G = min(G, len(kuyruk), len(yeni))
                kuyruk, kuyruk_son = kuyruk[:-G], kuyruk[-G:]
                for i in range(G):
                    w = yumusak((i + 1) / (G + 1))
                    yeni[i] = u8(kuyruk_son[i].astype(np.float32) * (1 - w) + yeni[i].astype(np.float32) * w)
            else:
                yeni = yeni[1:]                # ortak anahtar kare iki kez görünmesin
        if s.get("karart_gir"):
            m = s["karart_gir"] * FPS
            yeni = [u8(k.astype(np.float32) * yumusak(i / m)) if i < m else k for i, k in enumerate(yeni)]
        yaz(kuyruk)
        kuyruk = yeni
        print(f"{s.get('ad', tur)}: {len(yeni)} kare ({len(yeni) / FPS:.2f} sn), geçiş {G} kare", flush=True)
    yaz(kuyruk)
    enc.stdin.close()
    enc.wait()
    print(cikti, f"{n / FPS:.2f} sn")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 22)
