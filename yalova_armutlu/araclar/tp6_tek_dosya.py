# yalova_armutlu_16blok.py + tp6_plan.py -> tek başına çalışan yalova_armutlu_tp6.py.
# Taban sahne aynen alınır; T_P-6 tanımları yerleşim / peyzaj / rapor / blok_tipi'nin yerine geçer.
# Kullanım: python3 tp6_tek_dosya.py   (yalova_armutlu/ altına yazar)
import os
import re

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
taban = open(os.path.join(KOK, "yalova_armutlu_16blok.py"), encoding="utf-8").read()
tp6 = open(os.path.join(KOK, "tp6_plan.py"), encoding="utf-8").read()

BASLIK = '''# -*- coding: utf-8 -*-
"""
YALOVA · ARMUTLU · KARŞIYAKA MAH. (Tavşantepe Mevkii, Pafta 39/2)
PARSEL 7104 (5.648 m²) + 7105 (4.510 m²) · T_P-6 VAZİYET PLANI (Katar Mühendislik Mimarlık, etüt)
14 BLOK · ZEMİN + 4 = 5 KAT · 350 DAİRE
  7104 (kuzeyden güneye): 2 büyük blok (katta 8 adet 1+1), 4 standart blok (katta 4 adet 2+1),
                          kıyıda yan yana 2 küçük blok (katta 3 adet 2+1)
  7105: 2 standart + 2 büyük + 2 standart blok

Mimari önceki çalışmalarla aynı: traverten cephe, koyu kat silmeleri, yuvarlak köşeli balkonlar,
çerçevesiz cam korkuluk, bronz doğrama. Blok şekilleri ve yerleri T_P-6 planından (1/500 PDF) ölçüldü.

Blender 4.2 – 5.x · Cycles (GPU önerilir)
Arayüzden : Scripting sekmesi > Open > bu dosya > Run Script  (sahne kurulur; render için F12)
            Kameralar: CAM_TP6_KOSE (sunum açısı, etkin), CAM_TP6_ORTADAN, CAM_TP6_UST (tepeden plan)
Konsoldan : blender -b -P yalova_armutlu_tp6.py -- --render  [--cikti KLASOR] [--ornek N]
            [--onizleme] (düşük çözünürlük, hızlı)  [--cevrimdisi] (internet yok, prosedürel malzeme)

İlk çalıştırmada Poly Haven'dan (CC0, ücretsiz) altın saat gökyüzü HDRI'ı ve PBR dokular indirilir
(~60 MB, bir kez; ~/Yalova_Armutlu_Render/polyhaven altında saklanır). İnternet yoksa prosedürel
malzemelerle devam eder.

Bu dosya araclar/tp6_tek_dosya.py ile yalova_armutlu_16blok.py ve tp6_plan.py'den üretildi.
"""
'''

# taban: modül açıklaması yerine yeni başlık, sondaki çalıştırma bloğu çıkar
govde = taban[taban.index('"""', taban.index('"""') + 3) + 3:].lstrip("\n")
govde = govde[:govde.rindex('\nif __name__ == "__main__":')].rstrip() + "\n"

# tp6: açıklama, importlar, G sözlüğü ve uygula() çıkar; _icinde taban sahnedekiyle çakışmasın
t = tp6[tp6.index('"""', tp6.index('"""') + 3) + 3:]
t = re.sub(r"^import (math|random)\n", "", t, flags=re.M).lstrip("\n")
t = t.replace('G = {}                                   # 16blok.py modül sözlüğü (uygula ile dolar)\n', "")
t = t[:t.index("\ndef uygula(ns):")].rstrip() + "\n"
t = re.sub(r"\b_icinde\(", "_hucrede(", t)

KOPRU = '''

# ============================== T_P-6 ==============================
# Taban sahnenin blok tipi (T_P-4 bloğu) standart bloklar için kalır; büyük ve küçük bloklar hücreden
# kurulur. Aşağıdaki yerlesim / peyzaj / rapor tabandakilerin yerine geçer.
G = globals()
_blok_tipi_t4 = blok_tipi

'''

SON = '''

def blok_tipi(M, coll, ad, t):
    return blok_tipi_genel(M, coll, ad, t) if t.get("tur") == "genel" else _blok_tipi_t4(M, coll, ad, t)


BLOK_TIPLERI = TIPLER


def tp6_kameralar(sc):
    """Sunumdaki köşe açısı (K2), ortadan kuşbakışı ve tepeden ortografik plan görünüşü."""
    coll = bpy.data.collections["KAMERA_ISIK"]
    t = bpy.data.objects.get("TEKNELER")             # köşe kadrajında yat alt kenarda kalmasın
    if t:
        for v in t.data.vertices:
            if (v.co.x - 112.0) ** 2 + (v.co.y + 106.0) ** 2 < 81.0:
                v.co.x -= 7.8
                v.co.y += 9.1
    T0 = Vector((22.4, -46.0, 0.0))
    yon = Vector((138.0 - 22.4, -221.0 + 46.0, 0.0)).normalized()
    D3 = (Vector((138.0, -221.0, 70.0)) - T0).length
    e = math.radians(28.0)
    kose = kamera("CAM_TP6_KOSE", tuple(T0 + yon * D3 * math.cos(e) + Vector((0, 0, D3 * math.sin(e)))),
                  tuple(T0), 42.0, coll)
    orta = kamera("CAM_TP6_ORTADAN", (-1.0, -199.0, 147.0), (-1.0, -24.0, 0.0), 35.0, coll)
    cd = bpy.data.cameras.new("CAM_TP6_UST")
    cd.type = 'ORTHO'
    cd.ortho_scale = 175.0
    cd.clip_start, cd.clip_end = 1.0, 2000.0
    ust = bpy.data.objects.new("CAM_TP6_UST", cd)
    ust.location = (-1.0, -4.0, 400.0)
    coll.objects.link(ust)
    sc.camera = kose
    return kose, orta, ust


def tp6_render(sc, kameralar):
    os.makedirs(CIKTI_KLASORU, exist_ok=True)
    w, h = COZ_GENEL
    for cam, dosya, coz in zip(kameralar, ("tp6_kose.png", "tp6_ortadan.png", "tp6_ust_plan.png"),
                               ((w, h), (w, h), (int(h * 0.7), h))):
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = coz
        sc.render.filepath = os.path.join(CIKTI_KLASORU, dosya)
        bpy.ops.render.render(write_still=True, scene=sc.name)
        print("Kaydedildi:", sc.render.filepath)
    sc.camera = kameralar[0]
    sc.render.resolution_x, sc.render.resolution_y = w, h


if __name__ == "__main__":
    gc.disable()                         # yüz binlerce geometri listesi: kurulumu hızlandırır
    try:
        _sc, _sc2 = kur()
    finally:
        gc.enable()
    _kam = tp6_kameralar(_sc)
    if OTOMATIK_RENDER:
        tp6_render(_sc, _kam)
'''

cikti = os.path.join(KOK, "yalova_armutlu_tp6.py")
open(cikti, "w", encoding="utf-8").write(BASLIK + govde + KOPRU + t + SON)
print(cikti, sum(1 for _ in open(cikti, encoding="utf-8")), "satır")
