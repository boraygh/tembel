# Yalova Armutlu – 8 + 7 blok: gerçekçi drone + yaya turu

`yalova_armutlu_8_7_gercekci.mp4` — 1920×1080, 24 fps, 85,3 sn, sessiz. Repodaki kopya CRF 24'tür (45 MB).
Teslim edilen ana kopya CRF 17'dir (112 MB). Bu v3.1'dir: girişten sonraki bütün video tek reçeteyle yeniden üretildi;
son klip bir önceki klibin bitmiş görüntüsünden zincirleme devam ettirildi.

> **Görsel çalışmadır.** Kamera yolu ve bütün yapıların yeri, Blender modelinden birebir gelir. Kling yalnızca
> yüzeyleri gerçekçileştirdi. Birkaç yerde küçük yorumlar ekledi: ağaç türleri, sokak ağaçları, panoramada
> kendi bloğun balkonu. Komşu evler ve kıyı düzeni temsilidir.

| Süre | Sahne | Etiket |
|---|---|---|
| 0–16,3 sn | Denizden, iki parselin arasındaki sokaktan en arkadaki sol bloğa yaklaşma | "8 + 7 BLOK · DENİZ MANZARASI / YALOVA ARMUTLU", sonra 15. BLOK |
| 16,4–42,7 sn | Sol sıranın köşelerinden, en üst kat hizasında arkadan öne yavaş kayma | EN ÜST KAT · 15 → 1. BLOK |
| 42,8–53,7 sn | En öndeki 1. bloğun balkonundan panorama | EN ÜST KAT · PANORAMA |
| 53,8–57,9 sn | Hızlı dönüş, yaya hizasına iniş | — |
| 57,9–80,8 sn | Yaya hizasında sahile yürüyüş | YAYA HİZASI |
| 80,8–85,3 sn | ERDEM İNŞAAT kapanış kartı | |

Blok numaraları denizden başlar. Sol (7104) sıra arkadan öne 15, 13, …, 3, 1; sağ (7105) sıra 14, 12, …, 2.
Sağ altta mini vaziyet planı yer alır: etkin blok turuncu, kamera noktası ve bakış konisi canlı.

## v3 reçetesi (`araclar/v3/`, `araclar/final_kurgu_v3.py`)

v2'de her bölüm farklı istem ve referanslarla üretildiği için görünüm bölümden bölüme değişiyordu (9. saniyedeki
sıçrama dahil). v3'te giriş (ilk 9 sn, `kling/sonuc_1.mp4`) standart kabul edildi. Kalan video, `plan.py`'deki 6 klip
halinde aynı reçeteyle yeniden üretildi:

1. **Girdi:** `python3 parca_v3.py İLK SON çıktı.mp4`. Blender karelerine `on_duzelt.py` ile girişin tonu verilir:
   siyah noktası 34, sıcak denge, tepede %22 sıcak pus. Bu düzeltme olmadan Kling koyu, gölgeli sokağı neredeyse
   değiştirmiyordu (N1 klibinde 324. kareden sonra korelasyon 0,97).
2. **Referanslar (her klipte aynı düzen):**
   - bir önceki klibin geçiş karesi (süreklilik);
   - girişten stil karesi (`STIL_KARE = 150`);
   - klibin içerik çapası. Çapa, Nano Banana Pro 2K ile girişin görünümünde üretilmiş gerçek fotoğraftır.
3. **İstem:** tek metin (`plan.ISTEM`): "Transform this rough, untextured 3D previsualisation…". Önceki
   sürümlerdeki "fine film grain" ifadesi kaldırıldı; karıncalanmanın kaynağı oydu. İstem zamansal kararlılığı
   açıkça ister.
4. **Kurgu:** `python3 final_kurgu_v3.py çıktı.mp4 kapanis.mp4`.
   - Geçişler kameranın yavaş olduğu anlarda, 16 karelik çapraz geçişle yapılır (`plan.GECIS`).
   - Renk eşleme kanal başına kazanç ve ofsettir; 2 sn içinde söner.
   - Her klibe aynı hafif zamansal gürültü giderme uygulanır (`hqdn3d=0:0:3:3`).
   - v2'deki bölüm bazlı ton ve görünüm düzeltmeleri (`bakis.py`, gama) artık kullanılmıyor.
5. **Son klip, zincirleme (v3.1):** İlk M5, M4'ten farklı bir sokak sonu çiziyordu: 1:08'de palmiyeli deniz
   manzarası puslu bir tepe kasabasına dönüşüyordu. Çapa fotoğrafındaki iki araba da kutu gibi yer tutucu kalmıştı,
   Kling onları aynen taşıdı. Son ~4 sn'de deniz, karşısında kasaba olan bir koya dönüşüyordu. M5z bu sorunları
   şöyle çözüyor:
   - **Girdi:** `python3 parca_zincir.py sonuc_m4.mp4 1276 1604 1620 8 1940 m_5z.mp4`. Girdi M4'ün bitmiş son
     16 karesiyle başlar, 8 karede tonlanmış Blender karelerine harmanlanır. Blender karelerinin rengi bağ noktasında
     M4'e eşlenir ve eşleme 4 sn'de söner.
   - **Çapa:** Nano Banana ile düzeltilmiş 1800 çapası (`cipa_1800z`): gerçek sedanlar, açık deniz, ufukta gemi.
   - **Sonuç:** Kling bitmiş kareleri neredeyse aynen korudu (M4'le korelasyon 0,99, renk farkı 2–3 seviye). Geçiş
     bu kısımda, 1604–1620 arasında yapılır. 1:08'deki görüntü tek parça; arabalar gerçek; son sahne açık deniz ve
     gemi. Kamera sona kadar Blender'ı izler.
   - **Bitiş:** Kamera 1940. karede (80,8 sn) durur; video burada biter, kapanış kartı buradan girer (`plan.SON`).

Bütün iş ve medya kimlikleri `v3/isler.json` dosyasında.

### Ölçümler (tam video, `v3/olc_final.py`, `v3/kipirti.py`)

- **Geçişler:** İçerik benzerliği 0,86–0,99. Geçiş pencerelerinde kareler arası en büyük parlaklık farkı 2,6,
  netlik farkı 1,4 (0–255 ölçeğinde). Bu ölçüm sıçramayı yakalar, iki klibin aynı sahneyi farklı çizmesini yakalamaz:
  27 ve 41. saniyedeki geçişlerde komşu klipler farklı içerik çiziyor (palmiye ve arabalar ekleniyor, ev
  kayboluyor). Bunlar ancak zincirleme yeniden üretimle düzelir. 1:08 geçişi zincirleme yapıldı (en büyük kare
  farkı 0,75, netlik farkı 0,22).
- **Karıncalanma:** Hareket telafili ince doku kıpırtısının doku enerjisine oranı ölçüldü.

  | Bölüm | Oran |
  |---|---|
  | Giriş | 0,19 |
  | Kayma | 0,17 |
  | Yürüyüş | 0,20 |
  | Panorama | 0,34 |

  Kayma ve yürüyüş girişle aynı düzeyde. Panoramadaki yüksek oran denizdeki dalga hareketinden geliyor. Mutlak
  kıpırtı kayma ve yürüyüşte girişten düşüktür.

### Bilinen sınırlar

- **M1→M2 (27 sn) ve M2→M3 (41 sn):** Komşu klipler aynı kareyi farklı çiziyor; geçişte içerik değişimi görülüyor.
  Düzeltmek için M1 ve M3 zincirleme yeniden üretilmeli (~56 kredi).
- **M3:** Batı panoramasında sağa blok benzeri bir yapı eklemiş.

## İlk üretim akışı (v1/v2, `araclar/`)

1. **Kamera yolu:** `rota.py` her kare için konum, yön ve bölüm verir (1978 kare, 24 fps).
   Temsili yük gemisi `gemi87.py` ile eklenir.
2. **Girdi render'ı (Blender, kredisiz):**
   `blender -b --factory-startup -P onizleme_blender.py -- --coz 1280x720 --ornek 8 --klasor kareler_hq`.
   - Cycles CPU, ~11 sn/kare, toplam ~4,5 saat.
   - Yürüyüş ve kayma hattındaki araç, ağaç ve direkler kaldırıldı; yürüyüş zemini `zemin.json`'a ışın atılarak bulundu.
3. **Bölümler:** `bolumler.py`, 8 bölüm. Her bölüm tam saniyedir, çünkü Kling süreyi aşağı yuvarlayarak ücretlendiriyor.
4. **Çapalar:** Nano Banana Pro 2K, "kompozisyon kilidi" komutu (`istemler.py → cipa`). Blender'daki yuvarlak,
   düşük poligonlu ağaçlar burada gerçek palmiye, zeytin ve fıstık çamına çevrildi.
5. **Video:** Kling 3.0 Omni Edit (`kling_video_edit`, pro). Her çıktı `vv_kontrol.py` ile denetlendi; kare
   kayması `hizala.py` ile ölçüldü (kayma 0, Kling 1 fazla kare veriyor). İş kimlikleri `isler_final.json` dosyasında.
6. **Kurgu:** `final_kurgu.py`. v2 bölüm 2–8'e `bakis.py` ile yumuşatma, parlama ve pus ekledi. Bu yöntem sıçramayı
   azalttı ama bölümler arasındaki farkı kapatmadı; v3 bu yüzden yapıldı.

## Maliyet

Higgsfield:

| Kalem | Kredi |
|---|---|
| v1/v2: Kling Omni Edit pro, 9 klip, 101 sn × 2 | 202 |
| v1/v2: Nano Banana Pro 2K çapa, 5 adet | 10 |
| v3: Kling Omni Edit pro, N1 15 sn + M1–M5 5 × 15 sn, × 2 | 180 |
| v3: Nano Banana Pro 2K stil çapası, 10 deneme | 20 |
| v3.1: Kling Omni Edit pro, M5z 14 sn × 2 | 28 |
| v3.1: Nano Banana Pro 2K çapa düzeltmesi | 2 |
| **Toplam** | **442** |

Blender render'ı kredisiz.
