# Balkon manzarası karelerinin kaplamaları (1920x1080 RGBA):
#   sağ altta mini vaziyet planı (8 + 9 blok, etkin blok turuncu, bakış konisi),
#   sol altta blok etiketi ("A BLOK" / "EN ÜST KAT · DENİZ MANZARASI").
#   Açılış için başlık kaplaması.
# Kullanım: python3 harita.py   -> kaplama_S1..S8.png, kaplama_A0.png
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "video", "araclar"))
from filigran import BEYAZ, TURUNCU, YAZI_KALIN, YAZI_ORTA, _font

D = os.path.dirname(os.path.abspath(__file__))
W, H, SS = 1920, 1080, 4
ZEMIN = (10, 13, 18)
DENIZ = (34, 86, 116)
PLAN = json.load(open(f"{D}/plan.json"))
KAM = json.load(open(f"{D}/kameralar.json"))
HARF = "ABCDEFGH"

U0, U1, V0, V1 = -58.0, 52.0, -172.0, 80.0  # harita penceresi (m)
OLC = 1.15                                   # px / m (1080p'de)
PAD, BAS = 14, 30                            # kenar payı, başlık yüksekliği (px)
MW, MH = round((U1 - U0) * OLC), round((V1 - V0) * OLC)
PW, PH = MW + 2 * PAD, MH + 2 * PAD + BAS
KENAR = 44                                   # kare kenarından boşluk (px)


def m2p(u, v):
    """metre -> panel tuvali (SS ölçekli) piksel"""
    return ((PAD + (u - U0) * OLC) * SS, (PAD + BAS + (V1 - v) * OLC) * SS)


def kontur(b):
    return [(b["u"] + x, b["v"] + y) for x, y in PLAN["kontur"][b["tip"]]]


def panel(etkin=None):
    """etkin: 0..7 (sol sıradaki blok, A = en arka) ya da None. Panel RGBA (SS ölçekli) döner."""
    P = Image.new("RGBA", (PW * SS, PH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(P, "RGBA")
    d.rounded_rectangle([0, 0, PW * SS - 1, PH * SS - 1], 12 * SS, fill=ZEMIN + (205,))
    # harita alanı ayrı katmanda, sonra yuvarlak köşeli pencereyle kırpılır
    M = Image.new("RGBA", P.size, (0, 0, 0, 0))
    g = ImageDraw.Draw(M, "RGBA")
    k = sorted(PLAN["KIYI"], key=lambda p: p[0])
    g.polygon([m2p(u, v) for u, v in k + [(k[-1][0], V0 - 80), (k[0][0], V0 - 80)]], fill=DENIZ + (255,))
    g.line([m2p(u, v) for u, v in PLAN["SAHIL_YOLU"]], fill=(140, 146, 156, 170), width=round(2.0 * SS))
    for p in ("P7104", "P7105"):
        pts = [m2p(u, v) for u, v in PLAN[p]]
        g.line(pts + [pts[0]], fill=BEYAZ + (110,), width=round(1.0 * SS))
    sol = sorted((b for b in PLAN["bloklar"] if b["parsel"] == "7104"), key=lambda b: -b["v"])
    for b in PLAN["bloklar"]:
        if b["parsel"] == "7105":
            g.polygon([m2p(u, v) for u, v in kontur(b)], fill=BEYAZ + (80,))
    if etkin is not None:
        kam = KAM[f"S{etkin + 1}"]
        cx, cy = kam["konum"][:2]
        hx, hy = kam["hedef"][:2]
        a0, yari, L = math.atan2(hy - cy, hx - cx), math.atan(18.0 / kam["lens"]), 260.0
        kenar = [(cx + L * math.cos(a0 + yari * t), cy + L * math.sin(a0 + yari * t)) for t in np.linspace(-1, 1, 9)]
        mk = Image.new("L", P.size, 0)
        ImageDraw.Draw(mk).polygon([m2p(cx, cy)] + [m2p(u, v) for u, v in kenar], fill=255)
        x0, y0 = m2p(cx, cy)
        yy, xx = np.mgrid[0:P.size[1], 0:P.size[0]]
        r = np.hypot(xx - x0, yy - y0) / (L * OLC * SS * 0.85)
        a = np.asarray(mk, np.float32) / 255 * np.clip(1 - r, 0, 1) ** 1.1 * 185
        koni = Image.new("RGBA", P.size, TURUNCU + (0,))
        koni.putalpha(Image.fromarray(a.astype(np.uint8)))
        M.alpha_composite(koni)
        g = ImageDraw.Draw(M, "RGBA")
    for i, b in enumerate(sol):
        g.polygon([m2p(u, v) for u, v in kontur(b)], fill=(TURUNCU + (255,)) if i == etkin else (BEYAZ + (230,)))
    if etkin is not None:
        x, y = m2p(*KAM[f"S{etkin + 1}"]["konum"][:2])
        rr = 2.6 * SS
        g.ellipse([x - rr, y - rr, x + rr, y + rr], fill=BEYAZ + (255,), outline=ZEMIN + (255,), width=round(0.8 * SS))
    pen = Image.new("L", P.size, 0)
    ImageDraw.Draw(pen).rounded_rectangle([PAD * SS, (PAD + BAS) * SS, (PW - PAD) * SS, (PH - PAD) * SS], 7 * SS, fill=255)
    M.putalpha(Image.fromarray(np.minimum(np.asarray(M.getchannel("A")), np.asarray(pen))))
    P.alpha_composite(M)
    d = ImageDraw.Draw(P, "RGBA")
    f = _font(YAZI_KALIN, 8.0 * SS)
    for i, b in enumerate(sol):
        x, y = m2p(min(u for u, v in kontur(b)) - 3.5, b["v"])
        d.text((x, y), HARF[i], font=f, anchor="rm", fill=(TURUNCU + (255,)) if i == etkin else (BEYAZ + (170,)))
    d.text((PAD * SS, (PAD + 13) * SS), "VAZİYET", font=_font(YAZI_ORTA, 8.5 * SS), anchor="ls", fill=BEYAZ + (215,))
    kx, ky = (PW - PAD - 4) * SS, (PAD + 8) * SS
    d.polygon([(kx, ky - 7 * SS), (kx - 4.5 * SS, ky + 6 * SS), (kx, ky + 3 * SS), (kx + 4.5 * SS, ky + 6 * SS)], fill=BEYAZ + (230,))
    d.text((kx - 9 * SS, ky + 3 * SS), "K", font=_font(YAZI_KALIN, 7.5 * SS), anchor="rm", fill=BEYAZ + (230,))
    x, y = m2p(-30, -160)
    d.text((x, y), "DENİZ", font=_font(YAZI_ORTA, 7.0 * SS), anchor="mm", fill=BEYAZ + (200,))
    return P


def perde(katman, kutu, guc):
    """Yazının arkasına yumuşak koyu geçiş (okunurluk)."""
    x0, y0, x1, y1 = (v * SS for v in kutu)
    m = Image.new("L", katman.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], 40 * SS, fill=int(255 * guc))
    m = m.filter(ImageFilter.GaussianBlur(30 * SS))
    k = Image.new("RGBA", katman.size, ZEMIN + (0,))
    k.putalpha(m)
    katman.alpha_composite(k)


def aralikli(d, x, taban, metin, font, renk, ara):
    for ch in metin:
        d.text((x, taban), ch, font=font, anchor="ls", fill=renk)
        x += font.getlength(ch) + ara
    return x


def etiket(katman, harf):
    x, taban = 64, H - 70
    perde(katman, (x - 70, taban - 150, x + 560, taban + 60), 0.55)
    d = ImageDraw.Draw(katman, "RGBA")
    d.rectangle([x * SS, (taban - 96) * SS, (x + 46) * SS, (taban - 90) * SS], fill=TURUNCU + (255,))
    aralikli(d, x * SS, (taban - 66) * SS, "EN ÜST KAT  ·  DENİZ MANZARASI", _font(YAZI_ORTA, 19 * SS), BEYAZ + (235,), 2.2 * SS)
    d.text((x * SS, taban * SS), f"{harf} BLOK", font=_font(YAZI_KALIN, 58 * SS), anchor="ls", fill=BEYAZ + (255,))


def kaydet(katman, yol):
    katman.resize((W, H), Image.LANCZOS).save(yol)


if __name__ == "__main__":
    for i in range(8):
        k = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        etiket(k, HARF[i])
        k.alpha_composite(panel(i), ((W - KENAR - PW) * SS, (H - KENAR - PH) * SS))
        kaydet(k, f"{D}/kaplama_S{i + 1}.png")
    k = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    x, taban = 64, H - 64
    perde(k, (x - 80, taban - 215, x + 900, taban + 70), 0.72)
    d = ImageDraw.Draw(k, "RGBA")
    d.rectangle([x * SS, (taban - 168) * SS, (x + 46) * SS, (taban - 162) * SS], fill=TURUNCU + (255,))
    aralikli(d, x * SS, (taban - 136) * SS, "SOL SIRA  ·  8 BLOK", _font(YAZI_ORTA, 19 * SS), BEYAZ + (235,), 2.2 * SS)
    d.text((x * SS, (taban - 62) * SS), "EN ÜST KAT", font=_font(YAZI_KALIN, 46 * SS), anchor="ls", fill=BEYAZ + (255,))
    d.text((x * SS, taban * SS), "DENİZ MANZARALARI", font=_font(YAZI_KALIN, 46 * SS), anchor="ls", fill=BEYAZ + (255,))
    kaydet(k, f"{D}/kaplama_A0.png")
    print("kaplamalar tamam", PW, PH)
