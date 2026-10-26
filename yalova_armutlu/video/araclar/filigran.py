# ERDEM İNŞAAT filigranı: logodaki E işareti (vektörden yeniden çizilir) + iki satır yazı.
# Kullanım: python3 filigran.py GIRDI.png CIKTI.png [konum: sol_ust|sag_alt|sol_alt|sag_ust]
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BEYAZ = (237, 241, 248)          # logodaki beyaz (#EDF1F8)
TURUNCU = (255, 122, 41)         # logodaki turuncu (#FF7A29)
YAZI_KALIN = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
YAZI_ORTA = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
OLCEK = 0.055                    # işaret yüksekliği / sqrt(genişlik x yükseklik)
KENAR = 0.025                    # kenar boşluğu / sqrt(genişlik x yükseklik)
OPAKLIK = 0.92
SS = 4                           # süper örnekleme


def _font(yol, kep_yuk):
    """Büyük harf yüksekliği kep_yuk piksel olacak boyutta font."""
    f = ImageFont.truetype(yol, 1000)
    kep = -f.getbbox("H", anchor="ls")[1]
    return ImageFont.truetype(yol, max(1, round(1000 * kep_yuk / kep)))


def _yaz(d, x, taban, metin, font, renk, aralik=0.0):
    """Harf aralıklı yazı: kerning önekin uzunluğundan, aralık harf başına eklenir."""
    for i, ch in enumerate(metin):
        xx = x + font.getlength(metin[:i]) + i * aralik
        d.text((xx, taban), ch, font=font, fill=renk, anchor="ls")
    return font.getlength(metin) + (len(metin) - 1) * aralik


def kilit(S):
    """S piksel yüksekliğinde işaret + yazı kilidi (RGBA)."""
    N = S * SS
    u = N / 100.0
    f1 = _font(YAZI_KALIN, 0.50 * N)
    f2 = _font(YAZI_ORTA, 0.235 * N)
    bosluk = 0.34 * N
    t1 = 0.02 * N
    # iki satırın mürekkep (ink) kenarlarını hizala: sol kenar ve sağ kenar aynı
    sol1 = f1.getbbox("E", anchor="ls")[0]
    sag1 = f1.getlength("ERDE") + 4 * t1 + f1.getbbox("M", anchor="ls")[2]
    sol2 = f2.getbbox("İ", anchor="ls")[0]
    sag2_dogal = f2.getlength("İNŞAA") + f2.getbbox("T", anchor="ls")[2]
    aralik2 = max(0.0, ((sag1 - sol1) - (sag2_dogal - sol2)) / 5)
    w1 = sag1 - sol1
    W = int(N + bosluk + w1 + 0.1 * N)
    H = int(N * 1.08)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = 255
    # E işareti (100 birimlik ızgara: gövde 25, boşluk 2, kollar 21 kalınlık)
    d.rectangle([0, 0, 25 * u - 1, 100 * u - 1], fill=BEYAZ + (a,))
    d.rectangle([27 * u, 0, 100 * u - 1, 21 * u - 1], fill=BEYAZ + (a,))
    d.rectangle([27 * u, 79 * u, 100 * u - 1, 100 * u - 1], fill=BEYAZ + (a,))
    d.rectangle([27 * u, 39.5 * u, 78 * u - 1, 60.5 * u - 1], fill=TURUNCU + (a,))
    x0 = N + bosluk
    _yaz(d, x0 - sol1, 0.50 * N, "ERDEM", f1, BEYAZ + (a,), t1)
    _yaz(d, x0 - sol2, 1.00 * N, "İNŞAAT", f2, BEYAZ + (a,), aralik2)
    return im.resize((W // SS, H // SS), Image.LANCZOS)


def _perde(w, h, cx, cy, rx, ry, guc):
    """Filigranın arkasında kenarı görünmeyen yumuşak koyu geçiş (açık zeminde okunurluk)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    t = np.clip((r - 0.30) / 0.70, 0.0, 1.0)
    a = guc * (1.0 - t * t * (3.0 - 2.0 * t))
    p = Image.new("RGBA", (w, h), (12, 10, 9, 0))
    p.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return p


def uygula(girdi, cikti, konum="sol_ust", perde=0.0):
    """perde > 0: filigranın arkasına bu güçte (0-1) yumuşak koyu geçiş eklenir."""
    img = Image.open(girdi).convert("RGB")
    w, h = img.size
    k = (w * h) ** 0.5
    S = round(OLCEK * k)
    m = round(KENAR * k)
    lk = kilit(S)
    lw, lh = lk.size
    x = m if "sol" in konum else w - m - lw
    y = m if "ust" in konum else h - m - lh
    # yumuşak gölge (okunurluk) + yarı saydam kilit
    pad = round(0.25 * S)
    golge_a = lk.getchannel("A").point(lambda v: int(v * 0.45))
    golge = Image.new("RGBA", (lw + 2 * pad, lh + 2 * pad), (0, 0, 0, 0))
    golge.paste(Image.new("RGBA", (lw, lh), (0, 0, 0, 255)), (pad, pad), golge_a)
    golge = golge.filter(ImageFilter.GaussianBlur(0.07 * S))
    katman = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if perde > 0:
        katman.alpha_composite(_perde(w, h, x + lw / 2, y + lh / 2, lw * 0.95, lh * 1.9, perde))
    katman.alpha_composite(golge, (x - pad + round(0.02 * S), y - pad + round(0.03 * S)))
    lk.putalpha(lk.getchannel("A").point(lambda v: int(v * OPAKLIK)))
    katman.alpha_composite(lk, (x, y))
    out = Image.alpha_composite(img.convert("RGBA"), katman).convert("RGB")
    out.save(cikti, optimize=True)
    return (x, y, lw, lh)


if __name__ == "__main__":
    konum = sys.argv[3] if len(sys.argv) > 3 else "sol_ust"
    print(uygula(sys.argv[1], sys.argv[2], konum))
