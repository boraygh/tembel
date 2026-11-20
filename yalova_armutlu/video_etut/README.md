# Yalova Armutlu etüt tanıtım videosu

Müşteri etüdünün (`etut_plan.py`: 7104'te 6, 7105'te 5 blok, 6 kat) tanıtım videosu. Süre 1:30, 1920x1080, 24 fps.
Video 86 sn kamera yolu ve 4,5 sn kapanış kartından oluşur.

## Kurgu (rota.py)

1. **Yaklaşma:** Kamera denizden siteye yaklaşır.
2. **Kayma:** İki sıranın arasından geçer.
3. **Panorama:** Sahile döner, deniz ve gemi görünür.
4. **Yükseliş:** Yaya katına inmez, ortadan yukarı çıkar.
5. **Genişlik:** 1+1 daireli geniş bloklar gösterilir. Önce 5. ve 7. blok, sonra 6. blok; yazı "1+1 DAİRELER · KATTA 8 DAİRE".
6. **Otopark:** Kamera geriye, parsellerin arka (kuzey) ucundaki otoparka gider.
   - 85 park yeri, 73 temsili araç.
   - Kamera otoparkın üstünde döner. Yazı "PARSELLERİN ARKASINDA / OTOPARK"; mini planda otopark turuncu yanar.
7. **Deniz:** Kamera blokların üstünden sahile geri gelir ve denizin üstünde durur. Ardından kapanış kartı gelir.

## Üretim (8 + 7 v3 reçetesi, `araclar/v3/`)

### Girdi

- Blender kareleri: `onizleme_blender.py`, 2091 kare, 1280x720, 8 örnek.
- Girdi videosu: `parca.py duz 1` (ilk klip) ve `parca.py zincir K` (sonraki klipler). Ton düzeltmesi `on_duzelt` ile yapılır.
- Bütün klipler zincirleme üretilir: her klip, bir öncekinin bitmiş son kareleriyle başlar.

### Kling Omni Edit pro

- 7 klip, `plan.KLIP` aralıklarıyla.
- Referanslar: önceki klibin geçiş karesi, stil karesi ve Nano Banana Pro 2K içerik çapaları. Çapa kareleri: 150, 456, 744, 1040, 1350, 1600, 1900.

### Sapmalar ve nedenleri (iş kimlikleri `v3/isler.json`)

- **1300 çapası:** NB kareyi iki denemede de kırpıp yakınlaştırdı. Yerine 1350 kullanıldı.
- **4. klip, ilk deneme:** Bloklar yukarıdan görüldüğünde dokusuz kaldı. Yeniden üretimde bloklara yukarıdan bakan bir çapa ve istemde çatı tarifi (çakıl çatı, traverten merdiven kutusu) eklendi.
- **5. klip, ilk deneme:** Otoparkın arkasına, kara tarafına deniz ve gemi koydu. Yeniden üretimde:
  - istem "iç kesim, deniz yok" oldu;
  - deniz çeken stil karesi bu klipten çıkarıldı;
  - referanslar önceki kare ve blok/otopark çapaları oldu.

  6. klip de iç kesim olduğu için aynı düzenle üretildi.
- **Renk:** 5. ve 6. klip bir öncekine göre soğuk kaldı. `renk_esle.py` ile örtüşen karelerde kanal başına kazanç ve ofset hesaplanıp eşlendi.
- **Kontrol:** `kontrol.py` her klipte girdiyle kare hizasını (kayma 0) ve kenar korelasyonunu ölçer.

### Kurgu

`final_kurgu.py ÇIKTI.mp4 kapanis.mp4` şunları ekler:

- 16 karelik çapraz geçiş ve renk eşleme;
- blok etiketleri;
- canlı mini vaziyet planı;
- ERDEM İNŞAAT kapanış kartı.

### Teslim

`Yalova_Armutlu_Etut_Tanitim.mp4`: CRF 21, 82 MB. Ana kopya CRF 17, 144 MB. İkisi de repoya konmadı (boyut sınırı).

## Maliyet (Higgsfield)

| Kalem | Kredi |
|---|---|
| Kling Omni Edit pro, 7 klip + 2 yeniden üretim (119 sn x 2) | 238 |
| Nano Banana Pro 2K içerik çapası, 9 adet | 18 |
| Nano Banana Pro 4K fotoğraf: yakın çekim 44-46, köşe 47-48 | 20 |
| **Toplam** | **276** |
