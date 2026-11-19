# Müşteri etüdü (yalova_etüt 1-2, AutoCAD PDF): parsel köşeleriyle benzerlik dönüşümü, blok konturları,
# renkli daire poligonları ve yazı konumları model koordinatında (u doğu, v kuzey; parsel ekseni).
import json, math, sys
import numpy as np, cv2, pdfplumber
P7104 = [(-4.57, 72.91), (-6.02, 74.79), (-38.89, 75.20), (-39.86, 72.58), (-40.44, -82.01), (-4.01, -82.5)]
P7105 = [(3.43, -66.29), (38.40, -64.90), (33.16, 73.98), (5.47, 74.81), (3.37, 73.01)]
ESLEME = {   # PDF pt (x, y aşağı) -> model köşesi
    "etut1": [((460.3, 214.6), P7104[0]), ((456.0, 206.0), P7104[1]), ((351.7, 171.7), P7104[2]),
              ((343.0, 176.1), P7104[3]), ((181.3, 684.1), P7104[4]), (None, P7104[5])],
    "etut2": [((397.6, 254.8), P7105[2]), ((307.4, 225.1), P7105[3]), ((299.0, 229.5), P7105[4]),
              ((154.9, 680.8), P7105[0]), ((268.9, 712.9), P7105[1])],
}
def kesisim(p1, p2, p3, p4):
    a = np.array([[p2[0] - p1[0], p3[0] - p4[0]], [p2[1] - p1[1], p3[1] - p4[1]]])
    t = np.linalg.solve(a, [p3[0] - p1[0], p3[1] - p1[1]])
    return (p1[0] + t[0] * (p2[0] - p1[0]), p1[1] + t[0] * (p2[1] - p1[1]))
# 1. paftada GD köşe: doğu kenar ile güney kenarın kesişimi
ESLEME["etut1"][5] = (kesisim((460.3, 214.6), (293.2, 738.2), (299.0, 720.3), (181.3, 684.1)), P7104[5])
RENK = {(0.96863, 0.67059, 0.68235): "pembe", (0.92941, 0.12157, 0.14118): "kirmizi",
        (0.78431, 0.78824, 0.17647): "sari", (0.27059, 0.63529, 0.78824): "mavi", (0.50196, 0.54902, 0.55686): "gri"}
sonuc = {}
for f in ("etut1", "etut2"):
    A = np.array([(x, -y) for (x, y), _ in ESLEME[f]]); B = np.array([m for _, m in ESLEME[f]])
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd(a.T @ b); R = (U @ Vt).T
    s = S.sum() / (a ** 2).sum(); t = mb - s * R @ ma
    don = lambda x, y: tuple(s * R @ np.array([x, -y]) + t)
    art = np.linalg.norm(np.array([don(*p) for p, _ in ESLEME[f]]) - B, axis=1)
    print(f"{f}: ölçek {s:.4f} m/pt, dönme {math.degrees(math.atan2(R[1,0], R[0,0])):.2f}°, köşe sapması ort {art.mean():.2f} m, en büyük {art.max():.2f} m")
    with pdfplumber.open(f"pdf/{f}.pdf") as pdf:
        pg = pdf.pages[0]
        renkli, konturlar = [], []
        for c in pg.curves + pg.rects:
            pts = c.get("pts") or [(c["x0"], c["top"]), (c["x1"], c["top"]), (c["x1"], c["bottom"]), (c["x0"], c["bottom"])]
            col = c.get("non_stroking_color")
            if c.get("fill") and isinstance(col, (tuple, list)) and len(col) == 3:
                ad = RENK.get(tuple(round(v, 5) for v in col))
                if ad:
                    renkli.append((ad, [don(*p) for p in pts]))
            lw = round(c.get("linewidth", 0), 2)
            if lw == 1.44:
                konturlar.append([don(*p) for p in pts])
        for l in pg.lines:
            if f == "etut1" and round(l.get("linewidth", 0), 2) == 1.44:
                konturlar.append([don(l["x0"], l["top"]), don(l["x1"], l["bottom"])])
        yazi = []
        for w in pg.extract_words(keep_blank_chars=False, extra_attrs=["size"]):
            if any(k in w["text"].upper() for k in ("BALKON", "ASANS", "GİRİŞ", "GIRIS", "SALON", "DAİRE", "DAIRE")):
                yazi.append((w["text"], don((w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2)))
    # bina konturları: renkli poligonlar dolu, kalın konturlar çizgi; boşluklar doldurulur
    PX, U0, V0, W, H = 10.0, -60.0, -100.0, 120.0, 190.0
    img = np.zeros((int(H * PX), int(W * PX)), np.uint8)
    pix = lambda q: np.round(np.c_[(np.array(q)[:, 0] - U0) * PX, (V0 + H - np.array(q)[:, 1]) * PX]).astype(np.int32)
    for _, q in renkli:
        cv2.fillPoly(img, [pix(q)], 255)
    for q in konturlar:
        cv2.polylines(img, [pix(q)], False, 255, 2)
    cnts, hier = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bina = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w * h < (8 * PX) ** 2 or w > 50 * PX or h > 60 * PX:
            continue
        pol = cv2.approxPolyDP(c, 0.2 * PX, True)[:, 0, :]
        poly = [(px / PX + U0, V0 + H - py / PX) for px, py in pol]
        us, vs = [p[0] for p in poly], [p[1] for p in poly]
        bina.append(dict(u0=min(us), u1=max(us), v0=min(vs), v1=max(vs), kontur=poly))
    bina.sort(key=lambda b: -b["v1"])
    for i, b in enumerate(bina):
        print(f"  {i}: u {b['u0']:7.2f}..{b['u1']:7.2f} ({b['u1']-b['u0']:5.2f})  v {b['v0']:7.2f}..{b['v1']:7.2f} ({b['v1']-b['v0']:5.2f})  köşe {len(b['kontur'])}")
    for tx, (u, v) in yazi:
        print(f"     yazı {tx:12s} ({u:6.1f}, {v:6.1f})")
    sonuc[f] = dict(olcek=s, R=R.tolist(), t=t.tolist(), bina=bina, renkli=renkli, yazi=yazi)
json.dump(sonuc, open("etut.json", "w"), indent=1)
