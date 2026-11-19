# Tepeden ortografik önizlemenin üstüne T_P-6 planını (kırmızı) bindirir: PDF px -> pt -> model (u, v) -> görüntü px.
import json, sys
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
d = json.load(open("binalar.json"))
s, R, t = d["olcek"], np.array(d["R"]), np.array(d["t"])
W, H, OS, CU, CV = 1400, 2000, 175.0, -1.0, -4.0
mpp = OS / H
# pt -> model: [u, v] = s R [x, -y] + t ; model -> img: X = (u - CU)/mpp + W/2, Y = H/2 - (v - CV)/mpp
A_pt = s * R @ np.diag([1.0, -1.0])
A_img = np.array([[1 / mpp, 0], [0, -1 / mpp]])
M2 = A_img @ A_pt / (600 / 72)                      # px(600dpi) -> img
b2 = A_img @ (t - np.array([CU, CV])) + np.array([W / 2, H / 2])
M = np.c_[M2, b2]
plan = np.array(Image.open("tp6_600.png").convert("L"))
cizgi = 255 - cv2.warpAffine(255 - plan, M, (W, H), flags=cv2.INTER_AREA)
render = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32)
mask = (cizgi < 160)[..., None]
out = np.where(mask, np.array([255, 30, 30], np.float32), render * 0.85)
Image.fromarray(out.astype(np.uint8)).save(sys.argv[2], quality=90)
yan = np.concatenate([render.astype(np.uint8), np.repeat(cizgi[..., None], 3, 2)], 1)
Image.fromarray(yan).resize((1400, 1000)).save(sys.argv[2].replace(".jpg", "_yan.jpg"), quality=88)
