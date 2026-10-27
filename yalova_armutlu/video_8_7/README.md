# Yalova Armutlu – 8 + 7 blok: gerçekçi drone + yaya turu

`yalova_armutlu_8_7_gercekci.mp4` — 1920×1080, 24 fps, 86,9 sn, sessiz. Repodaki kopya CRF 24'tür (51 MB).
Teslim edilen ana kopya CRF 17'dir (135 MB).

> **Görsel çalışmadır.** Kamera yolu ve bütün yapıların yeri, Blender modelinden birebir gelir. Kling yalnızca
> yüzeyleri gerçekçileştirdi. Birkaç yerde küçük yorumlar ekledi: ağaç türleri, sokak ağaçları, panoramada
> kendi bloğun balkonu. Komşu evler ve kıyı düzeni temsilidir.

| Süre | Sahne | Etiket |
|---|---|---|
| 0–16,3 sn | Denizden, iki parselin arasındaki sokaktan en arkadaki sol bloğa yaklaşma | "8 + 7 BLOK · DENİZ MANZARASI / YALOVA ARMUTLU", sonra 15. BLOK |
| 16,4–42,7 sn | Sol sıranın köşelerinden, en üst kat hizasında arkadan öne yavaş kayma | EN ÜST KAT · 15 → 1. BLOK |
| 42,8–53,7 sn | En öndeki 1. bloğun balkonundan panorama | EN ÜST KAT · PANORAMA |
| 53,8–57,9 sn | Hızlı dönüş, yaya hizasına iniş | — |
| 57,9–82,4 sn | Yaya hizasında sahile yürüyüş | YAYA HİZASI |
| 82,4–86,9 sn | ERDEM İNŞAAT kapanış kartı | |

Blok numaraları denizden başlar. Sol (7104) sıra arkadan öne 15, 13, …, 3, 1; sağ (7105) sıra 14, 12, …, 2.
Sağ altta mini vaziyet planı yer alır: etkin blok turuncu, kamera noktası ve bakış konisi canlı.

## Üretim akışı (`araclar/`)

1. **Kamera yolu:** `rota.py` her kare için konum, yön ve bölüm verir (1978 kare, 24 fps).
   Temsili yük gemisi `gemi87.py` ile eklenir.
2. **Girdi render'ı (Blender, kredisiz):**
   `blender -b --factory-startup -P onizleme_blender.py -- --coz 1280x720 --ornek 8 --klasor kareler_hq`.
   - Cycles CPU, ~11 sn/kare, toplam ~4,5 saat.
   - Yürüyüş ve kayma hattındaki araç, ağaç ve direkler kaldırıldı; yürüyüş zemini `zemin.json`'a ışın atılarak bulundu.
3. **Bölümler:** `bolumler.py` 8 bölüm tanımlar. Her bölüm tam saniyedir, çünkü Kling süreyi aşağı yuvarlayarak
   ücretlendiriyor. Komşu bölümler en az 8 kare bindirir. Bölüm videosu `python3 parca.py İLK SON çıktı.mp4 kareler_hq`.
4. **Gerçek fotoğraf çapaları:** Nano Banana Pro 2K, "kompozisyon kilidi" komutu (`istemler.py → cipa`).
   - Kareler: 1 (yaklaşma), 3 (kayma), 4 ve 5a (sahil parkı), 7 (yaya).
   - Blender'daki yuvarlak, düşük poligonlu ağaçlar burada gerçek palmiye, zeytin ve fıstık çamına çevrildi
     (`referanslar/blender_*.jpg` → `referanslar/cipa_*.jpg`).
5. **Video:** Kling 3.0 Omni Edit (`kling_video_edit`, pro). Referanslar: bölüm videosu, bir önceki bölümün
   Kling karesi (süreklilik), çapa fotoğrafı ve cephe referansı.
   - Bölüm 1–3 için `istemler.py → kling`, bölüm 4–8 için daha sert `kling_guclu` istemi kullanıldı.
   - Her çıktı `vv_kontrol.py` (kenar korelasyonu ve yan yana pafta) ile denetlendi; kare kayması `hizala.py` ile ölçüldü
     (kayma 0, Kling 1 fazla kare veriyor).
   - Bütün iş ve medya kimlikleri `isler_final.json` dosyasında.
6. **Kurgu:** `python3 final_kurgu.py çıktı.mp4 kapanis.mp4`.
   - Geçiş: sonraki bölümün ilk 8 karesinde çapraz geçiş yapılır.
   - Renk eşleme: içerik benzerse, geçiş penceresinde kanal başına kazanç ve ofset uygulanır; bu düzeltme 2 sn içinde söner.
   - Ton: bölüm 7'de gölgeler açıldı (gama 0,8).
   - Yazılar ve mini plan `birlestir.py`'den gelir (`GENISLIK=1920`).

## Karşılaşılan sorunlar

- **Bölüm 2:** Son ~16 karede Kling 15. bloğu silip yerine boş arsa koydu. Bölüm 3 bu yüzden 368. kareden başlatıldı;
  geçiş, bölüm 2'nin sağlam olduğu yerde yapılıyor.
- **Bölüm 4:** İlk deneme kaynağı neredeyse hiç değiştirmedi (korelasyon 0,97). Çapa fotoğrafı ve sert istemle
  yeniden üretildi.
- **Bölüm 6:** İlk ~1,5 sn balkondan geri çekilme yerine doğrudan sokak görüntüsüyle başlıyor. 5→6 geçişi kısa
  bir çözülme gibi görünüyor; bu geçişte renk eşleme kapalı.
- **Bölüm 7:** Kling koyu, ters ışıklı sokağı az değiştirdi. Kurguda gölgeler açıldı.
- **Bölüm 8:** Kling son saniyelerde kamerayı Blender'dan biraz yavaş ilerletip açık çimen ve deniz manzarasında
  bitiriyor.

## Maliyet

Higgsfield, toplam 212 kredi:

| Kalem | Kredi |
|---|---|
| Kling Omni Edit pro, 9 klip (bölüm 4 iki kez), 101 sn × 2 | 202 |
| Nano Banana Pro 2K çapa, 5 adet | 10 |

Blender render'ı kredisiz.
