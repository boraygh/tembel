# v3 final kurgu: giriş (kling/sonuc_1.mp4) + tek reçeteyle üretilen 6 klip (v3/sonuc_N.mp4), hepsi girdiyle kare kare hizalı.
# Geçişler v3/plan.py'deki karelerde 16 karelik çapraz geçiş + renk eşleme; numaralı blok etiketi, canlı mini vaziyet planı,
# açılış başlığı, kapanış. Görünüm düzeltmesi yok: bütün klipler aynı reçeteden geliyor.
# Kullanım: python3 final_kurgu_v3.py CIKTI.mp4 [KAPANIS.mp4]
import os, subprocess, sys
os.environ["GENISLIK"] = "1920"
import numpy as np
from PIL import Image
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
sys.path.insert(0, os.path.join(D, "v3"))
import rota, plan
import birlestir as B

W, H, FPS = B.W, B.H, B.FPS
BOL = [plan.GIRIS] + plan.KLIP
V3 = os.path.join(D, os.environ.get("V3", "v3"))
YOL = [os.path.join(D, "kling", "sonuc_1.mp4"), os.path.join(V3, "sonuc_1.mp4")] + \
      [os.path.join(V3, f"sonuc_m{k}.mp4") for k in range(1, len(plan.KLIP))]
GBAS = [None] + plan.GECIS                                   # bölüm k'ye geçişin başladığı kare
G = plan.GECIS_UZ                                            # çapraz geçiş uzunluğu (kare)
SONUM = 48                                                  # renk eşlemenin geçişten sonra sönme süresi (kare)


def isle(k, f8):
    return f8.astype(np.float32)


SAKIN = "hqdn3d=0:0:3:3"                                     # hafif zamansal gürültü giderme (karıncalanma), her klipte aynı


def ffmpeg_oku(yol, w, h, sec=None):
    vf = f"{SAKIN},scale={w}:{h}:flags=lanczos" + (f",select='between(n\\,{sec[0]}\\,{sec[1] - 1})'" if sec else "")
    return subprocess.Popen(["ffmpeg", "-v", "error", "-i", yol, "-vf", vf, "-vsync", "0", "-f", "rawvideo",
                             "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)


def kareler_al(yol, sec, w=480, h=270):
    p = ffmpeg_oku(yol, w, h, sec)
    v = np.frombuffer(p.stdout.read(), np.uint8).reshape(-1, h, w, 3).astype(np.float32)
    p.wait()
    return v


def eslem():
    """Bölüm k'nin geçiş penceresindeki renk dağılımını bölüm k-1'inkine eşleyen kanal başına kazanç/ofset."""
    T = [None]
    for k in range(1, len(BOL)):
        a0, a1, g0 = BOL[k - 1][0], BOL[k][0], GBAS[k]
        onc = kareler_al(YOL[k - 1], (g0 - a0, g0 - a0 + G))
        son = kareler_al(YOL[k], (g0 - a1, g0 - a1 + G))
        benzer = np.corrcoef(onc.mean(0).mean(2).ravel(), son.mean(0).mean(2).ravel())[0, 1]
        if benzer < 0.75:                                   # içerik farklı (ör. 4->5, 5->6): eşleme yanlış yöne iter
            T.append(None)
            print(f"bölüm {k + 1} renk eşleme atlandı (benzerlik {benzer:.2f})", flush=True)
            continue
        mo, so = onc.reshape(-1, 3).mean(0), onc.reshape(-1, 3).std(0)
        ms, ss = son.reshape(-1, 3).mean(0), son.reshape(-1, 3).std(0)
        g = np.clip(so / np.maximum(ss, 1e-3), 0.85, 1.15)
        o = np.clip(mo - ms * g, -20, 20)
        T.append((g, o))
        print(f"bölüm {k + 1} renk eşleme: benzerlik {benzer:.2f}  kazanç {np.round(g, 3)}  ofset {np.round(o, 1)}", flush=True)
    return T


def kaynak(i):
    """Kare i için (bölüm, ağırlık) listesi: GBAS[k]'den başlayan G karede k-1'den k'ye çapraz geçiş."""
    k = max([0] + [j for j in range(1, len(BOL)) if GBAS[j] <= i])
    if k > 0 and i < GBAS[k] + G:
        w = (i - GBAS[k] + 1) / (G + 1)
        return [(k - 1, 1 - w), (k, w)]
    return [(k, 1.0)]


class Okuyucu:
    def __init__(self, k):
        self.k = k
        self.p = ffmpeg_oku(YOL[k], W, H)
        self.n = W * H * 3

    def sonraki(self):
        b = self.p.stdout.read(self.n)
        if len(b) != self.n:
            return None
        return isle(self.k, np.frombuffer(b, np.uint8).reshape(H, W, 3))

    def kapat(self):
        self.p.stdout.read()                                  # Kling'in fazladan verdiği kareleri boşalt
        self.p.stdout.close()
        self.p.wait()


def main(cikti, kapanis=None):
    T = eslem()
    K = rota.kareler()
    n = len(K)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
    acik, son = {}, {}

    def bolum_karesi(k, i):
        if k not in acik:
            acik[k] = Okuyucu(k)
            for _ in range(i - BOL[k][0]):                   # klip geçişten önce başlıyor: baştaki kareleri atla
                acik[k].sonraki()
        f = acik[k].sonraki()
        f = son[k] if f is None else f                       # Kling bir kare eksik verirse son kareyi tut
        son[k] = f
        if T[k] is not None:
            s = 1.0 if i < GBAS[k] + G else max(0.0, 1.0 - (i - GBAS[k] - G + 1) / SONUM)
            if s > 0:
                g, o = T[k]
                f = f + s * (f * g + o - f)
        return f

    son_etiket, degisim, son_kare = None, -9.0, None
    ilk, bitis = (int(v) for v in os.environ.get("DENEME", f"0 {plan.SON}").split())   # deneme: yalnızca bir aralığı yaz
    for i, q in enumerate(K):
        if i >= bitis:
            break
        t = i / FPS
        kay = kaynak(i)
        a = sum(w * bolum_karesi(k, i) for k, w in kay)
        for k in list(acik):
            if k < kay[0][0]:
                acik.pop(k).kapat()
        if i < ilk:
            continue
        im = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).convert("RGBA")
        bolum, blok = q["bolum"], q["blok"]
        if t < 5.0:
            al = min(1.0, max(0.0, (t - 0.6) / 0.5)) * min(1.0, max(0.0, (4.6 - t) / 0.5))
            if al > 0:
                im.alpha_composite(B.etiket("8 + 7 BLOK  ·  DENİZ MANZARASI", "YALOVA ARMUTLU", al))
        elif bolum in B.UST and (blok is not None or bolum == "yuruyus"):
            ad = (B.UST[bolum], f"{blok}. BLOK" if blok is not None else "")
            if ad != son_etiket:
                son_etiket, degisim = ad, t
            im.alpha_composite(B.etiket(ad[0], ad[1], min(1.0, (t - degisim) / 0.25 + 0.25)))
        if t > 1.0:
            p = B.panel(blok, q["x"], q["y"], q["h"])
            if t < 1.6:
                p.putalpha(p.getchannel("A").point(lambda v, f=(t - 1.0) / 0.6: int(v * f)))
            im.alpha_composite(p, (int(W - 30 - B.PW), int(H - 30 - B.PH)))
        kare = np.asarray(im.convert("RGB"))
        enc.stdin.write(kare.tobytes())
        son_kare = kare
        if i % 240 == 0:
            print(f"{i}/{n}", flush=True)
    for o in acik.values():
        o.kapat()
    if kapanis:
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", kapanis, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        kk = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
        GK = 14                                              # kapanışa 0,6 sn geçiş
        for j in range(len(kk)):
            if j < GK:
                w = (j + 1) / (GK + 1)
                enc.stdin.write(np.clip(son_kare * (1 - w) + kk[j] * w + 0.5, 0, 255).astype(np.uint8).tobytes())
            else:
                enc.stdin.write(kk[j].tobytes())
    enc.stdin.close()
    enc.wait()
    print(cikti, "tamam")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
