# Önizleme videosunu birleştirir: 12 fps render kareleri -> 24 fps (ara kare = komşuların harmanı),
# 1280x720'ye büyütme, numaralı blok etiketi, kamerayı canlı gösteren mini vaziyet planı, önizleme rozeti, kapanış.
# Kullanım: python3 birlestir.py CIKTI.mp4 [KAPANIS.mp4]
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import rota

W = int(os.environ.get("GENISLIK", 1280))             # final kurgu 1920 ile içe aktarır
H, FPS = W * 9 // 16, 24
OLC = W / 1920.0                                      # 1080p tasarım ölçülerini çözünürlüğe uyarla
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FM = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
BEYAZ, TURUNCU, ZEMIN, DENIZ = (237, 241, 248), (255, 122, 41), (10, 13, 18), (34, 86, 116)
PLAN = json.load(open(os.path.join(D, "plan87.json")))
sol = sorted((b for b in PLAN["bloklar"] if b["parsel"] == "7104"), key=lambda b: -b["v"])
sag = sorted((b for b in PLAN["bloklar"] if b["parsel"] == "7105"), key=lambda b: -b["v"])
NO = {b["ad"]: n for b, n in zip(sol, rota.HARF)} | {b["ad"]: n for b, n in zip(sag, rota.NO_SAG)}


def font(yol, px):
    return ImageFont.truetype(yol, max(8, int(round(px))))


# ---------------- mini vaziyet planı ----------------
U0, U1, V0, V1 = -58.0, 52.0, -172.0, 80.0
M_OLC, PAD, BAS, SS = 1.6 * OLC, 14 * OLC, 34 * OLC, 3
PW, PH = int((U1 - U0) * M_OLC + 2 * PAD), int((V1 - V0) * M_OLC + 2 * PAD + BAS)


def m2p(u, v):
    return ((PAD + (u - U0) * M_OLC) * SS, (PAD + BAS + (V1 - v) * M_OLC) * SS)


def kontur(b):
    return [(b["u"] + x, b["v"] + y) for x, y in PLAN["kontur"][b["tip"]]]


def panel_zemin(etkin):
    P = Image.new("RGBA", (PW * SS, PH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(P, "RGBA")
    d.rounded_rectangle([0, 0, PW * SS - 1, PH * SS - 1], 10 * SS * OLC * 1.2, fill=ZEMIN + (205,))
    M = Image.new("RGBA", P.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(M, "RGBA")
    k = sorted(PLAN["KIYI"], key=lambda p: p[0])
    g.polygon([m2p(u, v) for u, v in k + [(k[-1][0], V0 - 80), (k[0][0], V0 - 80)]], fill=DENIZ + (255,))
    g.line([m2p(u, v) for u, v in PLAN["SAHIL_YOLU"]], fill=(140, 146, 156, 170), width=int(2 * SS * OLC))
    for p in ("P7104", "P7105"):
        q = [m2p(u, v) for u, v in PLAN[p]]
        g.line(q + [q[0]], fill=BEYAZ + (110,), width=max(1, int(SS * OLC)))
    for b in sol + sag:
        renk = TURUNCU + (255,) if NO[b["ad"]] == etkin else (BEYAZ + (225,) if b in sol else BEYAZ + (150,))
        g.polygon([m2p(u, v) for u, v in kontur(b)], fill=renk)
    pen = Image.new("L", P.size, 0)
    ImageDraw.Draw(pen).rounded_rectangle([PAD * SS, (PAD + BAS) * SS, (PW - PAD) * SS, (PH - PAD) * SS], 6 * SS, fill=255)
    M.putalpha(Image.fromarray(np.minimum(np.asarray(M.getchannel("A")), np.asarray(pen))))
    P.alpha_composite(M)
    d = ImageDraw.Draw(P, "RGBA")
    f = font(FB, 10.5 * OLC * SS)
    for b in sol:
        x, y = m2p(min(u for u, v in kontur(b)) - 2.5, b["v"])
        d.text((x, y), str(NO[b["ad"]]), font=f, anchor="rm", fill=TURUNCU + (255,) if NO[b["ad"]] == etkin else BEYAZ + (200,))
    for b in sag:
        x, y = m2p(max(u for u, v in kontur(b)) + 2.5, b["v"])
        d.text((x, y), str(NO[b["ad"]]), font=f, anchor="lm", fill=BEYAZ + (170,))
    d.text((PAD * SS, (PAD + 13 * OLC) * SS), "VAZİYET", font=font(FM, 11 * OLC * SS), anchor="ls", fill=BEYAZ + (215,))
    return P


_zemin = {}


def panel(etkin, x, y, h):
    if etkin not in _zemin:
        _zemin[etkin] = panel_zemin(etkin)
    P = _zemin[etkin].copy()
    if U0 - 5 < x < U1 + 5 and V0 - 5 < y < V1 + 5:
        d = ImageDraw.Draw(P, "RGBA")
        a0, yari, L = math.radians(90 - h), math.atan(18.0 / 24.0), 55.0
        q = [m2p(x, y)] + [m2p(x + L * math.cos(a0 + yari * t), y + L * math.sin(a0 + yari * t)) for t in np.linspace(-1, 1, 7)]
        kat = Image.new("RGBA", P.size, (0, 0, 0, 0))
        ImageDraw.Draw(kat, "RGBA").polygon(q, fill=TURUNCU + (120,))
        pen = Image.new("L", P.size, 0)
        ImageDraw.Draw(pen).rounded_rectangle([PAD * SS, (PAD + BAS) * SS, (PW - PAD) * SS, (PH - PAD) * SS], 6 * SS, fill=255)
        kat.putalpha(Image.fromarray(np.minimum(np.asarray(kat.getchannel("A")), np.asarray(pen))))
        P.alpha_composite(kat)
        X, Y = m2p(x, y)
        r = 3.2 * OLC * SS
        ImageDraw.Draw(P).ellipse([X - r, Y - r, X + r, Y + r], fill=BEYAZ + (255,), outline=TURUNCU + (255,), width=int(SS))
    return P.resize((PW, PH), Image.LANCZOS)


# ---------------- yazılar ----------------
def perde_maskesi():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([-40, H - 190 * OLC, 620 * OLC, H + 40], 40, fill=150)
    return m.filter(ImageFilter.GaussianBlur(26))


PERDE = Image.new("RGBA", (W, H), ZEMIN + (0,))
PERDE.putalpha(perde_maskesi())


def aralikli(d, x, taban, metin, f, renk, ara):
    for ch in metin:
        d.text((x, taban), ch, font=f, anchor="ls", fill=renk)
        x += f.getlength(ch) + ara


def etiket(ust, buyuk, alfa):
    k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    k.alpha_composite(PERDE)
    d = ImageDraw.Draw(k, "RGBA")
    x, taban = 64 * OLC, H - 64 * OLC
    a = int(255 * alfa)
    d.rectangle([x, taban - 96 * OLC, x + 46 * OLC, taban - 90 * OLC], fill=TURUNCU + (a,))
    aralikli(d, x, taban - 66 * OLC, ust, font(FM, 19 * OLC), BEYAZ + (a,), 2.2 * OLC)
    if buyuk:
        d.text((x, taban), buyuk, font=font(FB, 58 * OLC), anchor="ls", fill=BEYAZ + (a,))
    return k


def rozet():
    k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(k, "RGBA")
    f = font(FB, 15 * OLC)
    metin = "BLENDER ÖNİZLEME · KREDİSİZ"
    w = f.getlength(metin)
    x1, y0 = W - 28 * OLC, 26 * OLC
    d.rounded_rectangle([x1 - w - 24 * OLC, y0, x1, y0 + 30 * OLC], 8 * OLC, fill=ZEMIN + (170,))
    d.text((x1 - 12 * OLC, y0 + 15 * OLC), metin, font=f, anchor="rm", fill=BEYAZ + (230,))
    return k


ROZET = rozet()
UST = {"yaklasma": "EN ÜST KAT", "kayma": "EN ÜST KAT", "panorama": "EN ÜST KAT  ·  PANORAMA", "yuruyus": "YAYA HİZASI"}


def main(cikti, kapanis=None):
    K = rota.kareler()
    n = len(K)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", cikti], stdin=subprocess.PIPE)
    onbellek = {}

    def oku(i):
        i = min(i - i % 2, (n - 1) - (n - 1) % 2)
        if i not in onbellek:
            onbellek.clear() if len(onbellek) > 6 else None
            onbellek[i] = np.asarray(Image.open(os.path.join(D, "kareler", f"k_{i:04d}.jpg")).convert("RGB")
                                     .resize((W, H), Image.LANCZOS), np.float32)
        return onbellek[i]

    son_etiket, degisim = None, -9.0
    son_kare = None
    for i, q in enumerate(K):
        t = i / FPS
        a = oku(i) if i % 2 == 0 or i + 1 >= n else 0.5 * (oku(i - 1) + oku(i + 1))
        im = Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8)).convert("RGBA")
        bolum, blok = q["bolum"], q["blok"]
        if t < 5.0:                                                  # açılış başlığı
            al = min(1.0, max(0.0, (t - 0.6) / 0.5)) * min(1.0, max(0.0, (4.6 - t) / 0.5))
            if al > 0:
                im.alpha_composite(etiket("8 + 7 BLOK  ·  DENİZ MANZARASI", "YALOVA ARMUTLU", al))
        elif bolum in UST and (blok is not None or bolum == "yuruyus"):
            ad = (UST[bolum], f"{blok}. BLOK" if blok is not None else "")
            if ad != son_etiket:
                son_etiket, degisim = ad, t
            im.alpha_composite(etiket(ad[0], ad[1], min(1.0, (t - degisim) / 0.25 + 0.25)))
        if t > 1.0:
            p = panel(blok, q["x"], q["y"], q["h"])
            if t < 1.6:
                p.putalpha(p.getchannel("A").point(lambda v, f=(t - 1.0) / 0.6: int(v * f)))
            im.alpha_composite(p, (int(W - 30 * OLC - PW), int(H - 30 * OLC - PH)))
        im.alpha_composite(ROZET)
        kare = np.asarray(im.convert("RGB"))
        enc.stdin.write(kare.tobytes())
        son_kare = kare
        if i % 240 == 0:
            print(f"{i}/{n}", flush=True)
    if kapanis:                                                      # kapanışa 0,6 sn geçiş
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", kapanis, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                            "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        kk = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
        G = 14
        for j in range(len(kk)):
            if j < G:
                w = (j + 1) / (G + 1)
                enc.stdin.write(np.clip(son_kare * (1 - w) + kk[j] * w + 0.5, 0, 255).astype(np.uint8).tobytes())
            else:
                enc.stdin.write(kk[j].tobytes())
    enc.stdin.close()
    enc.wait()
    print(cikti, "tamam")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
