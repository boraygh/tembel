# Yalova Armutlu – tanıtım videosu (B seçeneği: yükselen blok)

`yalova_armutlu_tanitim.mp4` — 1920×1080, 24 fps, 34,9 sn, sessiz (müzik paylaşım sırasında eklenir).

| Süre | Sahne |
|---|---|
| 0–5,5 sn | Siyahtan açılış, son genel kareden (K0) öndeki bloğa (7105-G) yaklaşma |
| 5,5–9,3 sn | Kamera sabit, blok yerinden 14 m yükselir, altındaki avlu açılır |
| 9,3–23,2 sn | Havadaki bloğun etrafında tam tur: deniz cephesi → doğu ucu → kuzey (giriş) cephesi, arkada deniz → batı ucu → güney |
| 23,2–29,9 sn | Blok yerine iner, kamera geri çekilip tüm siteye döner |
| 29,9–34,9 sn | ERDEM İNŞAAT logosu çizilir, altında "YALOVA · ARMUTLU" |

## Üretim akışı (`araclar/`)

1. **Anahtar kareler (Blender, kredisiz):** `blender -b --factory-startup -P anahtar_b.py -- --ornek 160` → `K1–K5_render.png`;
   `-- --maske` ile yumuşatma maskeleri (deniz görünen K3/K4 için `--holdout 12 --kiyi_pay 14`). Kameralar `kamera_b.py`.
2. **Yapay zekâ girdisi:** `python3 girdi_b.py K1 K3 K4 K5` (ağaç, komşu ev, araç, insan yumuşatılır; proje blokları keskin kalır).
   K2 sabit kamerada K1'in aynısı olsun diye: `siluet.py` (bloğun görünen silueti) + `python3 k2_bilesik.py`, Nano Banana
   çıktısı gelince `python3 k2_bilesik.py son K2_nb.png` (blok dışındaki her piksel K1 fotoğrafından).
3. **Fotogerçekçi kareler:** Nano Banana Pro 2K, tek görsel girdi. Farklı açıdaki kareye ikinci referans görsel vermek
   kompozisyonu bozuyor (referansı kopyalıyor). Her çıktı `dogrula.py` ile Blender karesine karşı karo karo denetlenir.
4. **Klipler:** Kling 3.0 Omni Frames (başlangıç + bitiş karesi, pro, 5 sn, sessiz). İş kimlikleri `higgsfield_isler.json`.
5. **Kurgu:** `python3 kapanis.py kapanis_g.mp4 5.0 0.6` ve `python3 kurgu.py plan_final.json yalova_armutlu_tanitim.mp4 22`
   (hız rampaları, ters oynatma, klip birleşimlerinde kısa çapraz geçiş; klipler `klipler/` altına indirilir).

Harcanan Higgsfield kredisi: 61,75 (6 kredi, referans görselin bozduğu ilk K3–K5 denemesine gitti).
