# 7104 / 7105 parsellerine farklı blok adetlerinin yerleşimi: bloklar arası net mesafe ve emsal.
from PIL import Image, ImageDraw, ImageFont
P7104 = [(-4.57, 72.91), (-6.02, 74.79), (-38.89, 75.20), (-39.86, 72.58), (-40.44, -82.01), (-4.01, -82.50)]
P7105 = [(3.43, -66.29), (38.40, -64.90), (33.16, 73.98), (5.47, 74.81), (3.37, 73.01)]
TIP = {"7104": dict(xb=12.92, yd=5.61, k=(-22.36, 64.30), g=(-20.86, -71.76), alan=5648.0),
       "7105": dict(xb=11.67, yd=6.15, k=(18.39, 63.37), g=(19.83, -54.54), alan=4510.0)}
SILME, BRUT, KAT = 0.25, 264.0, 5
FB = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FM = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"

def hesap(pid, n):
    t = TIP[pid]
    (u0, v0), (u1, v1) = t["k"], t["g"]
    ara = (v0 - v1) / (n - 1)
    net = ara - 2 * (t["yd"] + SILME)
    kaks = n * KAT * BRUT / t["alan"]
    return [(u0 + (u1 - u0) * k / (n - 1), v0 + (v1 - v0) * k / (n - 1)) for k in range(n)], net, kaks

S, PAD = 4.2, 30                                     # px/m
def panel(nsol, nsag, baslik):
    W, H = int(90 * S) + 2 * PAD, int(165 * S) + 2 * PAD + 150
    im = Image.new("RGB", (W, H), (250, 249, 246))
    d = ImageDraw.Draw(im)
    f1, f2, f3 = ImageFont.truetype(FB, 26), ImageFont.truetype(FM, 19), ImageFont.truetype(FB, 17)
    px = lambda x, y: (PAD + (x + 45) * S, PAD + 70 + (78 - y) * S)
    d.text((PAD, 14), baslik, font=f1, fill=(20, 20, 20))
    for P in (P7104, P7105):
        d.polygon([px(*p) for p in P], fill=(226, 232, 214), outline=(110, 120, 90))
    sonuc = {}
    for pid, n in (("7104", nsol), ("7105", nsag)):
        t = TIP[pid]
        mer, net, kaks = hesap(pid, n)
        kotu = net < 6.0
        renk = (205, 70, 60) if net < 3.0 else ((225, 150, 40) if kotu else (60, 110, 170))
        for u, v in mer:
            x0, y0 = px(u - t["xb"] - SILME, v + t["yd"] + SILME)
            x1, y1 = px(u + t["xb"] + SILME, v - t["yd"] - SILME)
            d.rectangle([x0, y0, x1, y1], fill=renk, outline=(30, 30, 30))
        sonuc[pid] = (n, net, kaks, renk)
    y = int(165 * S) + PAD + 78
    for pid, ad in (("7104", "Sol (7104)"), ("7105", "Sağ (7105)")):
        n, net, kaks, renk = sonuc[pid]
        d.rectangle([PAD, y + 4, PAD + 16, y + 20], fill=renk)
        d.text((PAD + 24, y), f"{ad}: {n} blok", font=f3, fill=(20, 20, 20))
        d.text((PAD + 24, y + 22), f"bloklar arası {net:.1f} m · emsal {kaks:.2f}", font=f2, fill=(70, 70, 70))
        y += 56
    d.text((px(-44, -79)[0], px(0, -84)[1] + 2), "deniz yönü ↓", font=f2, fill=(80, 100, 130))
    return im

paneller = [panel(8, 9, "İstenen: 8 + 9"), panel(8, 8, "8 + 8"), panel(8, 7, "Önerim: 8 + 7")]
W = sum(p.width for p in paneller) + 20 * (len(paneller) - 1)
out = Image.new("RGB", (W, paneller[0].height), (255, 255, 255))
x = 0
for p in paneller:
    out.paste(p, (x, 0)); x += p.width + 20
out.save("fizibilite_8_9.png")
for pid in ("7104", "7105"):
    for n in (6, 7, 8, 9):
        _, net, kaks = hesap(pid, n)
        print(f"{pid} {n} blok: bloklar arası net {net:.1f} m, emsal {kaks:.2f}")
