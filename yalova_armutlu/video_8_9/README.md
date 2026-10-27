# Yalova Armutlu – 8 + 9 blok: sol sıra en üst kat deniz manzaraları

`yalova_armutlu_8_9_deniz_manzarasi.mp4` — 1920×1080, 24 fps, 28,8 sn, sessiz (müzik paylaşım sırasında eklenir).

> **Görsel çalışmadır.** Mevcut blok tipiyle 7104'e 8 blok sığar (bloklar arası net 7,7 m, emsal ≈1,87).
> 7105'e 9 blok ancak 1,9 m arayla sığar (emsal ≈2,63) → `fizibilite_8_9.png`. Komşu evler temsilidir;
> gerçek komşu yapıların yerini ve yüksekliğini göstermez, manzara sonucu onlara göre değişebilir.

| Süre | Sahne |
|---|---|
| 0–5 sn | Siyahtan açılış, her zamanki köşe drone açısı, sol sıranın arkasına doğru yavaş yaklaşma; "SOL SIRA · 8 BLOK / EN ÜST KAT DENİZ MANZARALARI" |
| 5–22 sn | A → G: her bloğun en üst kat güneybatı köşe balkonundan sabit kamera, 2,4'er sn. Sol altta blok adı, sağ altta mini vaziyet planı (etkin blok turuncu, bakış konisi) |
| 22–25 sn | H blok (en ön), 3,75 sn |
| 25–28,8 sn | ERDEM İNŞAAT kapanış kartı, "YALOVA · ARMUTLU" |

Kamera: göz hizası 14,6 m (zemin + 4. kat), güneybatıya bakış (güneyden 25° batı), 24 mm, dikey kaydırma −0,12.
Kamera bloğun batı ucunda, güney cephedeki köşe balkonunda. A en arka (kuzey), H en ön (güney).

Sonuç: A–D'de deniz komşu evlerin arasından ve çatıların üstünden ince bir şerit olarak görünüyor. E–G'de bant
genişliyor ve G'de sahile kadar iniyor. H'de manzara kesintisiz: sahil, iskele ve açık deniz.
Ufuk çizgisi ve görünen deniz alanı her karede Blender karesiyle aynı. Yapay zekâ yalnızca dokuları
gerçekçileştirdi, manzarayı büyütmedi (`kareler/*_blender.jpg` ile karşılaştırılabilir).

## Üretim akışı (`araclar/`)

1. **Kareler (Blender, kredisiz):** `blender -b --factory-startup -P manzara.py -- --ornek 160` (önizleme için `--onizle`,
   yumuşatma maskeleri ve kıyı hattı için `--maske`). Ana betik `--sol 8 --sag 9` ile çağrılır, kameralar `kameralar.json`.
2. **Yapay zekâ girdisi:** `python3 girdi_v89.py A0 S1 S2 S3 S4 S5 S6 S7 S8`. Komşu evler ve ağaçlar yumuşatılır,
   deniz tarafı hiç yumuşatılmaz.
3. **Fotogerçekçi kareler:** Nano Banana Pro 2K, tek görsel girdi, "kompozisyon kilidi" komutu. Her çıktı
   `python3 kontrol.py AD NB.png` ile Blender karesine karşı denetlendi: hizalama, karo korelasyonu, ufuk çizgisi.
   Açık alanlı F ve H ilk denemede kadrajı değiştirdi; nesne konumları yüzdeyle tarif edilerek tekrarlandı.
   C, D, F ve H'ye ikinci bir gerçekçilik turu yapıldı. Bu tur yolları çukurlu, sıvaları lekeli gösterince
   üzerine bir "bakımlı mahalle" turu daha yapıldı.
4. **Klipler:** Kling 3.0 Omni Frames (pro, sessiz).
   - Açılış 5 sn: bitiş karesi açılış karesinin %20 yakın kırpımı.
   - Balkonlar 3 sn, sabit kamera; H 4 sn.
   - `klip_kontrol.py` ile kamera kayması ölçüldü. C'nin ilk klibi yana döndüğü için yeniden üretildi.
5. **Kurgu:**
   - `plan_dok.py` (Blender) vaziyet verisini `plan.json`'a döker.
   - `python3 harita.py` kaplamaları üretir.
   - `python3 ../../video/araclar/kapanis.py kapanis_v89.mp4 4.5 0.4` kapanış kartını üretir.
   - `python3 kurgu_v89.py plan_v89.json CIKTI.mp4 20` videoyu birleştirir. Klipler `araclar/klipler/` altına indirilir.

Harcanan Higgsfield kredisi: 79,25.
- Nano Banana Pro 2K: 19 iş, 38 kredi.
- Kling: 41,25 kredi.

İş kimlikleri `araclar/isler.json` içinde.
