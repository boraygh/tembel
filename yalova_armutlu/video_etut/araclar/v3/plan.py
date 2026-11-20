# Etüt videosu, 8 + 7 videosunun v3.1 reçetesiyle: Blender girdisi on_duzelt.py ile girişin tonuna çekilir, istem
# "Transform this rough ... previsualisation" ile açılır; referanslar stil karesi, içerik çapası ve (2. klipten itibaren)
# bir önceki klibin bitmiş karesi. 8 + 7'de yalnızca son klip zincirlenmişti (1:08 düzeldi, 27 / 41 sn geçişleri
# zincirsiz kaldığı için görünüm değişiyordu); burada bütün klipler zincirleme: her klibin girdisi bir öncekinin bitmiş
# son karelerinden başlar (parca.py zincir). Klipler bu yüzden sırayla üretilir.
#
# Kling Omni Edit süreyi tam saniyeye indirdiği için klip uzunlukları 24'ün katı (en çok 15 sn = 360 kare).
# Geçişler kameranın yavaşladığı / durduğu karelerde (rota.py hızları):
#   240  yaklaşma, uzakta, dönüş ~2°/sn          576  kaymada 7. blok durağı, 3,6 m/sn
#   888  panorama başı (dönüş 36°/sn, öteleme yok) 1176 ortadan yukarıda geri çekilip durduğu an (1 m/sn)
#   1464 otoparka giderken dönüş yönü değişir      1728 otoparkın üstünde dönüş biter, kamera durur
# Kamera 2054'te sahilin üstünde durur; video 2064'te biter, kapanış kartı buradan girer.
KLIP = [(0, 264), (240, 600), (576, 912), (888, 1200), (1176, 1488), (1464, 1752), (1728, 2088)]
GECIS = [240, 576, 888, 1176, 1464, 1728]   # klip k+1'e geçişin başladığı kare; GECIS_UZ kare sürer
GECIS_UZ = 16
ZINCIR_HARMAN = 8                     # zincirde komşu kareleri GECIS + GECIS_UZ'a kadar, sonra 8 karede Blender'a harman
SON = 2064
SANIYE = [(b - a) // 24 for a, b in KLIP]          # 11 + 15 + 14 + 13 + 13 + 12 + 15 = 93 sn -> 186 kredi (2 kr/sn)

# 8 + 7 videosunun stil karesi (giriş klibi sonuc_1, yerel kare 150): görünüm birebir aynı kalsın diye aynısı.
STIL_MEDIA = "d55e35af-4a00-4848-a630-aefaef36e173"
CIPA_KARE = [150, 456, 744, 1040, 1350, 1600, 1900]      # her klibin içerik çapası (Blender karesinin NB düzenlemesi)

ISTEM = ("Transform this rough, untextured 3D previsualisation into real footage filmed in Armutlu, Yalova, Turkey, "
         "with exactly the same look as the reference photographs: the same warm golden late-afternoon light with "
         "soft atmospheric haze, the same colours, contrast, softness and lens. Keep exactly the same camera path, "
         "speed, framing and timing, and the same layout: the same apartment blocks in the same places with the same "
         "number of floors and balconies, the same streets, open-air car parks, coast, pier, ship and trees; do not add, remove, merge or "
         "move anything. Re-render every surface as it looks in real footage: the new six-storey apartment blocks "
         "with real honed travertine stone cladding, very dark brown-anthracite floor slab bands wrapping the "
         "rounded-corner balconies, frameless glass balustrades with slim bronze handrails, real glass with "
         "reflections, real interiors with curtains and warm lamps; real fine-grained asphalt with white markings, "
         "granite kerbs, clipped hedges and lawns; the round, ball-shaped low-poly trees are placeholders: turn them "
         "into real Canary date palms, olive trees and Italian stone pines with natural foliage; the boxy placeholder "
         "cars are real modern cars; the town with real Turkish summer houses with terracotta roofs; the forested "
         "hillside; the real Sea of Marmara with gentle waves and a glittering sun path, and the long container ship "
         "on the horizon. Everything clean, new and well kept. The image must be temporally stable: no flicker, no "
         "shimmering or crawling textures, no grain, no warping, smooth natural motion. Real footage, not CGI: no "
         "plastic or toy-like surfaces, no text, no watermark.")

CIPA_ISTEM = ("Edit this image into a real, unretouched photograph: warm golden late-afternoon light with soft "
              "atmospheric haze, natural colours, gentle contrast and a real camera lens. Keep the composition "
              "exactly: do not move the camera, do not zoom, do not re-frame; every building, tree, car and object "
              "stays at exactly the same position, size and outline; do not add, remove or merge anything. Six-storey "
              "blocks with real honed travertine facades, very dark brown-anthracite slab bands, frameless glass "
              "balustrades with slim bronze handrails, real glass and interiors; the round, ball-shaped low-poly "
              "trees are placeholders: make them real Canary date palms, olive trees and Italian stone pines with "
              "natural foliage; real asphalt, kerbs, hedges and lawns; real modern cars; real sea with sun glitter. "
              "Clean, new and well kept. No CGI or toy-like look, no grain, no text, no watermark.")
