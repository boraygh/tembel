# Görünüm standardı: bölüm 1'in (giriş) puslu altın ışığı. Bölüm 2'nin ilk karelerini bölüm 1'in aynı içerikli son
# kareleriyle 6 yatay bantta karşılaştırınca fark bir atmosfer pusu çıktı: açık nötr bir katman, tepede ~%25,
# aşağı doğru sıfıra iniyor; bölüm 1 ayrıca ~%20 daha yumuşak. Bölüm 2-8'e yumuşatma + ince parlama + bu pus uygulanır.
import numpy as np
from PIL import Image, ImageFilter

YUMUSAK, PARLAMA_R, PARLAMA_A = 0.7, 12, 0.12
PUS_RENK = np.array([218.0, 214.0, 208.0], np.float32)
PUS_TEPE, PUS_US = 0.25, 1.6


def yumusat(f8):
    p = Image.fromarray(f8)
    f = np.asarray(p.filter(ImageFilter.GaussianBlur(YUMUSAK)), np.float32)
    return (1 - PARLAMA_A) * f + PARLAMA_A * np.asarray(p.filter(ImageFilter.GaussianBlur(PARLAMA_R)), np.float32)


_alfa = {}


def pus(f):
    h = f.shape[0]
    if h not in _alfa:
        _alfa[h] = (PUS_TEPE * (1 - (np.arange(h) + 0.5) / h) ** PUS_US).astype(np.float32)[:, None, None]
    a = _alfa[h]
    return f * (1 - a) + PUS_RENK * a


def uygula(f8):
    return pus(yumusat(f8))
