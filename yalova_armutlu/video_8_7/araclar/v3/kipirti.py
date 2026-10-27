# Hareket telafili ince doku kıpırtısı (karıncalanma) ve aynı bölgenin doku enerjisi; oran = kıpırtı / doku.
import subprocess, sys, numpy as np, cv2
w, h = 640, 360
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
def oku(yol, a, b, vf_ek=""):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", yol, "-vf", f"select='between(n\\,{a}\\,{b-1})'{vf_ek},scale={w}:{h}",
                        "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w).astype(np.float32)
def olc(v):
    r, t = [], []
    for i in range(0, len(v) - 1, 3):
        f = dis.calc(v[i + 1].astype(np.uint8), v[i].astype(np.uint8), None)
        hz = cv2.remap(v[i], gx + f[..., 0], gy + f[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        d = (v[i + 1] - hz)[20:-20, 20:-180]
        r.append(np.abs(d - cv2.GaussianBlur(d, (0, 0), 3)).mean())
        s = v[i + 1][20:-20, 20:-180]
        t.append(np.abs(s - cv2.GaussianBlur(s, (0, 0), 3)).mean())
    return np.mean(r), np.mean(t)
if __name__ == "__main__":
    for ad, (a, b) in {"yaklaşma": (100, 200), "kayma": (600, 700), "panorama": (1100, 1200), "yürüyüş": (1700, 1800)}.items():
        s = []
        for yol in sys.argv[1:]:
            r, t = olc(oku(yol, a, b))
            s.append(f"kıpırtı {r:.2f} doku {t:.2f} oran {r / t:.3f}")
        print(f"{ad:10s}", " | ".join(s))
