# Zincirde komşu klibin rengine kayan klibi bütünüyle düzeltir: örtüşen karelerde kanal başına kazanç/ofset
# python3 renk_esle.py ONCEKI.mp4 ONCEKI_BAS SONRAKI.mp4 ORTUSME_UZ CIKTI.mp4
import subprocess, sys, numpy as np
on, ob, so, n, cik = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), sys.argv[5]
def oku(p, sec, w=480, h=270):
    r = subprocess.run(["ffmpeg","-v","error","-i",p,"-vf",f"select='between(n\\,{sec[0]}\\,{sec[1]})',scale={w}:{h}","-vsync","0","-f","rawvideo","-pix_fmt","rgb24","-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w, 3).astype(np.float32)
A = oku(on, (ob, ob + n - 1)).reshape(-1, 3); B = oku(so, (0, n - 1)).reshape(-1, 3)
g = np.clip(A.std(0) / np.maximum(B.std(0), 1e-3), 0.8, 1.25)
o = A.mean(0) - B.mean(0) * g
print("kazanç", g.round(3), "ofset", o.round(1))
W, H = 1920, 1080
d = subprocess.Popen(["ffmpeg","-v","error","-i",so,"-f","rawvideo","-pix_fmt","rgb24","-"], stdout=subprocess.PIPE)
e = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","24","-i","-",
                      "-c:v","libx264","-preset","slow","-crf","14","-pix_fmt","yuv420p","-movflags","+faststart",cik], stdin=subprocess.PIPE)
k = 0
while True:
    b = d.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32)
    e.stdin.write(np.clip(f * g + o + 0.5, 0, 255).astype(np.uint8).tobytes()); k += 1
e.stdin.close(); e.wait(); d.wait()
print(cik, k, "kare")
