# v3 reçetesi, Kling'e giden Blender girdisi için ön düzeltme (bütün kliplerde aynı). Girişte Kling'in yaptığı ton dönüşümü:
# gölgeler kaldırılmış (siyah ~35), hafif sıcak ton, yumuşak kontrast ve üstte atmosfer pusu. Koyu, gölgeli render kareleri
# böylece Kling'e zaten girişin ışığında gider; Kling kareyi az değiştirse bile görünüm standarttan sapmaz.
import numpy as np

SIYAH, BEYAZ = 34.0, 250.0
SICAK = np.array([1.04, 1.0, 0.94], np.float32)
PUS_RENK = np.array([226.0, 214.0, 196.0], np.float32)
PUS_TEPE, PUS_US = 0.22, 1.6
_alfa = {}


def duzelt(f):
    """f: (h, w, 3) uint8/float -> float 0-255."""
    x = f.astype(np.float32) / 255.0
    x = x ** 0.92                                               # orta tonları hafif aç
    y = SIYAH + x * (BEYAZ - SIYAH)                             # gölgeleri kaldır, en parlakları yumuşat
    y = y * SICAK
    h = y.shape[0]
    if h not in _alfa:
        _alfa[h] = (PUS_TEPE * (1 - (np.arange(h) + 0.5) / h) ** PUS_US).astype(np.float32)[:, None, None]
    a = _alfa[h]
    return np.clip(y * (1 - a) + PUS_RENK * a, 0, 255)
