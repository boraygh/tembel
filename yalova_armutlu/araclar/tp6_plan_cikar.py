# T_P-6 vaziyet planından (1/500 PDF) bina konturları: PDF pt -> model (u, v) benzerlik dönüşümü,
# kalın duvar çizgileri (lw 0.84) rasterleştirilip bağlı bileşenlere ayrılır.
import json, math, sys
import numpy as np, cv2, pdfplumber
PDF = sys.argv[1]
P7104 = [(-4.57, 72.91), (-6.02, 74.79), (-38.89, 75.20), (-39.86, 72.58), (-40.44, -82.01), (-4.01, -82.5)]
P7105 = [(3.43, -66.29), (38.40, -64.90), (33.16, 73.98), (5.47, 74.81), (3.37, 73.01)]
with pdfplumber.open(PDF) as pdf:
    p = pdf.pages[0]
    parsel = [c for c in p.curves if (c["bottom"] - c["top"]) > 500]
    sol = max(parsel, key=lambda c: -c["x0"])["pts"]; sag = max(parsel, key=lambda c: c["x0"])["pts"]
    pdf_pts = [sol[0], sol[1], sol[2], sol[3], sol[4], sol[5], sag[0], sag[1], sag[2], sag[3], sag[4]]
    mod_pts = [P7104[0], P7104[1], P7104[2], P7104[3], P7104[4], P7104[5],
               P7105[2], P7105[3], P7105[4], P7105[0], P7105[1]]
    A = np.array([(x, -y) for x, y in pdf_pts]); B = np.array(mod_pts)
    ma, mb = A.mean(0), B.mean(0); a, b = A - ma, B - mb
    U, S, Vt = np.linalg.svd(a.T @ b); R = (U @ Vt).T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = (U @ Vt).T
    s = S.sum() / (a ** 2).sum(); t = mb - s * R @ ma
    don = lambda x, y: s * R @ np.array([x, -y]) + t
    art = np.array([don(*q) - m for q, m in zip(pdf_pts, mod_pts)])
    print(f"ölçek {s:.5f} m/pt (1/{s / (25.4 / 72 / 1000):.0f}), dönme {math.degrees(math.atan2(R[1,0], R[0,0])):.2f}°, "
          f"artık ort {np.linalg.norm(art, axis=1).mean():.2f} m, en büyük {np.linalg.norm(art, axis=1).max():.2f} m")
    seg = []
    for l in p.lines:
        if round(l.get("linewidth", 0), 2) == 0.84:
            seg.append([(l["x0"], l["top"]), (l["x1"], l["bottom"])])
    for c in p.curves:
        if round(c.get("linewidth", 0), 2) == 0.84 and (c["bottom"] - c["top"]) < 500:
            seg.append(c["pts"])
PX = 20.0                                              # px / m
U0, V0, W, H = -60.0, -100.0, 120.0, 190.0
img = np.zeros((int(H * PX), int(W * PX)), np.uint8)
for pl in seg:
    q = np.array([don(x, y) for x, y in pl])
    q = np.round(np.c_[(q[:, 0] - U0) * PX, (V0 + H - q[:, 1]) * PX]).astype(np.int32)
    cv2.polylines(img, [q], False, 255, 3)
cv2.imwrite("duvar.png", img)
kap = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(kap)
bina = []
for i in range(1, n):
    x, y, w, h, alan = st[i]
    if w * h < (6 * PX) ** 2: continue
    m = (lab == i).astype(np.uint8) * 255
    dol = m.copy(); ff = np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, 0.15 * PX, True)[:, 0, :]
    poly = [((px / PX) + U0, V0 + H - py / PX) for px, py in c]
    us = [p[0] for p in poly]; vs = [p[1] for p in poly]
    bina.append(dict(u0=min(us), u1=max(us), v0=min(vs), v1=max(vs), kontur=poly))
bina.sort(key=lambda b: (int((b["u0"] + b["u1"]) / 2 > 0), -b["v1"]))
for i, b in enumerate(bina):
    print(f"{i:2d}  u {b['u0']:7.2f}..{b['u1']:7.2f} ({b['u1']-b['u0']:5.2f})  v {b['v0']:7.2f}..{b['v1']:7.2f} ({b['v1']-b['v0']:5.2f})  "
          f"merkez ({(b['u0']+b['u1'])/2:6.2f}, {(b['v0']+b['v1'])/2:6.2f})  köşe {len(b['kontur'])}")
json.dump(dict(olcek=s, R=R.tolist(), t=t.tolist(), bina=bina), open("binalar.json", "w"), indent=1)
