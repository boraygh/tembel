# v3: giriş (bölüm 1, Kling sonuc_1) standarttır; kalan video tek reçeteyle 6 klip halinde yeniden üretilir.
# Her klip: aynı istem, aynı stil karesi (girişten), girişin stilinde üretilmiş içerik çapası, bir önceki klibin karesi.
# Geçişler kameranın yavaş olduğu anlarda, 16 kare.
GIRIS = (0, 216)                       # kling/sonuc_1.mp4
# N1 (168-528) ilk reçeteyle üretildi; 324'ten sonra Kling gölgeli sokakta Blender'ı neredeyse değiştirmedi (kor 0,97).
# Kalan 5 klip (M1-M5) aynı reçetenin kesin hâliyle: Blender girdisi on_duzelt.py ile girişin tonuna çekilir,
# istem "Transform this rough ... previsualisation" ile açılır.
# v3.1: son klip (M5z) M4'ün bitmiş son 16 karesiyle başlayan zincirleme girdiyle yeniden üretildi (parca_zincir.py):
# 1:08'deki görüntü değişimi, yer tutucu arabalar ve sondaki koy/gemi sorunu için.
KLIP = [(168, 528), (308, 668), (625, 985), (932, 1292), (1276, 1636), (1604, 1940)]
SON_KLIP = "sonuc_m5z.mp4"
GECIS = [170, 308, 652, 969, 1276, 1604]    # her klibe geçişin başladığı kare (öncekinden bu klibe), 16 kare sürer
GECIS_UZ = 16
# Kamera ~1940'ta durur; Kling'in ilk M5'i bundan sonra kendi başına öne atılıp bulanıklaşıyordu (netlik 6,8 -> 2,8).
# Video burada biter, kapanış kartı buradan çapraz geçişle girer.
SON = 1940
STIL_KARE = 150                        # girişten stil karesi (sonuc_1 yerel kare)
CIPA_KARE = [348, 668, 928, 1168, 1500, 1800]
KLIP_CIPA = [348, 348, 668, 1168, 1500, 1800]  # her klibin içerik çapası

ISTEM_N1 = ("Re-shoot this scene as real footage in Armutlu, Yalova, Turkey, with exactly the same look as the reference "
         "photographs: the same warm golden late-afternoon light with soft atmospheric haze, the same colours, "
         "contrast, softness and lens. Keep exactly the same camera path, speed, framing and timing, and the same "
         "layout: the same apartment blocks in the same places with the same number of floors and balconies, the same "
         "streets, coast, pier, ship and trees; do not add, remove, merge or move anything. Re-render every surface as "
         "it looks in real footage: the new five-storey apartment blocks with real honed travertine stone cladding, "
         "very dark brown-anthracite floor slab bands wrapping the rounded-corner balconies, frameless glass "
         "balustrades with slim bronze handrails, real glass with reflections, real interiors with curtains and warm "
         "lamps; real fine-grained asphalt with white markings, granite kerbs, clipped hedges and lawns; the round, "
         "ball-shaped low-poly trees are placeholders: turn them into real Canary date palms, olive trees and Italian "
         "stone pines with natural foliage; the town with real Turkish summer houses with terracotta roofs; the "
         "forested hillside; the real Sea of Marmara with gentle waves and a glittering sun path, and the long "
         "container ship on the horizon. Everything clean, new and well kept. The image must be temporally stable: "
         "no flicker, no shimmering or crawling textures, no grain, no warping, smooth natural motion. Real footage, "
         "not CGI: no plastic or toy-like surfaces, no text, no watermark.")

CIPA_ISTEM = ("Edit the first image into a real, unretouched photograph with exactly the photographic look of the second "
              "image: the same warm golden late-afternoon light with soft atmospheric haze, the same colours, contrast, "
              "softness and lens. Keep the composition of the first image exactly: do not move the camera, do not zoom, "
              "do not re-frame; every building, tree, car and object stays at exactly the same position, size and "
              "outline; do not add, remove or merge anything. Use the second image only for the look, not for its "
              "content. Real honed travertine facades with very dark brown-anthracite slab bands, frameless glass "
              "balustrades with slim bronze handrails, real glass and interiors; the round, ball-shaped low-poly trees "
              "are placeholders: make them real Canary date palms, olive trees and Italian stone pines with natural "
              "foliage; real asphalt, kerbs, hedges and lawns; real sea with sun glitter. Clean, new and well kept. "
              "No CGI or toy-like look, no grain, no text, no watermark.")


ISTEM = ("Transform this rough, untextured 3D previsualisation into real footage filmed in Armutlu, Yalova, Turkey, "
         "with exactly the same look as the reference photographs" + ISTEM_N1[ISTEM_N1.index(": the same warm"):])
