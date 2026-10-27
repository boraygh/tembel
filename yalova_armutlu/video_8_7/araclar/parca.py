# Render karelerinden (kareler/k_XXXX.jpg, 24 fps) Kling'e gidecek bölüm videosu: 1920x1080'e Lanczos, CRF 16.
# Kullanım: python3 parca.py ILK_KARE SON_KARE(dahil değil) CIKTI.mp4
import os, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
a, b, cikti = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
KL = sys.argv[4] if len(sys.argv) > 4 else "kareler"
eksik = [i for i in range(a, b) if not os.path.exists(os.path.join(D, KL, f"k_{i:04d}.jpg"))]
if eksik:
    sys.exit(f"eksik kare: {len(eksik)} (ilk {eksik[:5]})")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-start_number", str(a), "-i",
                os.path.join(D, KL, "k_%04d.jpg"), "-frames:v", str(b - a),
                "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", cikti], check=True)
print(cikti, f"{(b - a) / 24:.2f} sn")
