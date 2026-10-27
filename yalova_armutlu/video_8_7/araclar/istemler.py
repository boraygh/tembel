# Final için Higgsfield istemleri: bölüm başına Nano Banana Pro çapası (orta kare -> gerçek fotoğraf) ve Kling Omni Edit.
# Kullanım: python3 istemler.py N  -> bölüm N'in çapa karesi ile iki istemi JSON olarak yazar.
import json, sys
import bolumler

CEKIM = {
    1: ("drone", "The drone starts high over the open Sea of Marmara and flies towards the coast of Armutlu: deep blue sea "
        "with natural waves, a glittering golden sun path and a few small boats; a curved sandy beach with umbrellas, a "
        "seaside promenade with real Canary palms and a coastal lawn; the small town with real two and three storey "
        "Turkish summer houses with terracotta tile roofs, rooftop solar water heaters and balconies; the two new rows of "
        "apartment blocks in the middle; and behind the town a real steep hillside covered with dense stone pine, olive "
        "and oak forest with natural depth, texture and light."),
    2: ("drone", "The drone descends and flies up the new street between the two rows of new apartment blocks at top-floor "
        "height, away from the sea; at the end of the street real Turkish summer houses with terracotta tile roofs and a "
        "real steep hillside covered with dense stone pine and olive forest."),
    3: ("drone", "The drone glides slowly at top-floor height along the corners of the left row of apartment blocks towards "
        "the sea, passing close to the rounded top-floor balconies; at the end of the street the real Sea of Marmara with "
        "a glittering golden sun path and the long container ship on the horizon."),
    4: ("drone", "The drone glides slowly at top-floor height along the corners of the left row of apartment blocks towards "
        "the sea, passing close to the rounded top-floor balconies, and arrives at the front block; ahead, the coastal "
        "lawn with real Canary palms and olive trees, the sandy beach, the real Sea of Marmara with a glittering golden "
        "sun path and the long container ship on the horizon."),
    5: ("drone", "A slow panorama from the top-floor balcony of the front block over the coast: a real coastal lawn and "
        "promenade with real Canary palms and olive trees with natural irregular foliage, a real sandy beach with "
        "umbrellas, a small concrete pier, the real Sea of Marmara with gentle waves, turquoise shallows and a glittering "
        "golden sun path towards the low sun, and the long container ship on the horizon."),
    6: ("drone", "Still facing the sea, the drone flies quickly backwards up the new street between the two rows of "
        "apartment blocks and descends to eye level; at the end of the street the real Sea of Marmara and the long "
        "container ship on the horizon."),
    7: ("yaya", "An eye-level walk down the new street between the two rows of new apartment blocks towards the sea; the "
        "blocks rise on both sides with their garden walls and hedges, and at the end of the street the coast with real "
        "Canary palms and a glimpse of the sea."),
    8: ("yaya", "An eye-level walk down the new street between the two rows of new apartment blocks to the coast, arriving "
        "at the seaside lawn and promenade with real Canary palms and olive trees, the sandy beach and the real Sea of "
        "Marmara with a glittering golden sun path and the long container ship on the horizon. The street in the "
        "shade of the blocks is bright and airy, filled with soft daylight bounce as in the reference photographs, "
        "never dark."),
}

BINA = ("The new five-storey apartment blocks, with exactly the design of the reference images: real honed travertine "
        "stone cladding with natural veining, visible joints and subtle colour variation, very dark brown-anthracite "
        "floor slab bands wrapping the rounded-corner balconies, frameless glass balustrades with slim bronze handrails, "
        "real glass reflecting the sky and the opposite buildings, real interiors with curtains and warm lamps, teak "
        "outdoor furniture, potted olive trees. "
        "The street: real fine-grained dark asphalt with crisp white markings, real granite kerbstones and paving, "
        "clipped boxwood hedges, real lawn grass and a few real parked cars. Everything clean, new and well kept.")

# Blender'daki ağaçlar düşük poligonlu yer tutucular; Kling şekillerini koruyup oyuncak gibi bırakıyor (bölüm 1)
AGAC = ("The round, ball-shaped and low-poly trees of the source are placeholders: turn them into real trees with natural, "
        "irregular, airy canopies, visible branches and moving leaves: real Canary date palms with full feathery fronds "
        "and textured trunks, real olive trees and Italian stone pines.")

ISIK = ("Warm golden late-afternoon sun with long soft shadows and soft bounce light in the shades, gentle atmospheric "
        "haze towards the sea, real camera exposure with natural highlight roll-off, true-to-life colours, fine film "
        "grain, crisp real-world detail.")

KAMERA = {"drone": "real footage filmed with a professional full-frame cinema drone",
          "yaya": "real footage filmed at eye level with a gimbal-stabilised full-frame cinema camera"}


def kling(n):
    tur, sahne = CEKIM[n]
    return (f"Re-shoot this scene as {KAMERA[tur]} in Armutlu, Yalova, Turkey: ultra-photorealistic, indistinguishable "
            "from a real video. Keep exactly the same camera path, speed, framing and timing, and the same layout: the "
            "same apartment blocks in the same places with the same number of floors and balconies, the same street, "
            "coast, ship and trees; do not add, remove, merge or move anything. Re-render every surface as it looks in "
            f"real footage, matching the photographic look of the reference images. {sahne} {BINA} {AGAC} {ISIK} Real "
            "footage, not CGI: no plastic, glossy or toy-like surfaces, no flicker, no warping, no text, no watermark.")


def kling_guclu(n):
    """Kling'in kaynağı neredeyse hiç değiştirmediği bölümler için (bölüm 4 ilk deneme) daha sert dönüşüm istemi."""
    tur, sahne = CEKIM[n]
    return (f"Transform this rough, untextured 3D previsualisation into {KAMERA[tur]} in Armutlu, Yalova, Turkey: "
            "ultra-photorealistic, with exactly the look of the reference photographs. Keep exactly the same camera "
            "path, speed, framing and timing, and the same layout: the same apartment blocks in the same places with the "
            "same number of floors and balconies, the same street, coast, pier, ship and trees; do not add, remove, merge "
            f"or move anything. Every surface must change from CGI to real. {sahne} {BINA} {AGAC} {ISIK} Real "
            "footage, not CGI: no plastic, glossy or toy-like surfaces, no flicker, no warping, no text, no watermark.")


def cipa(n):
    tur, sahne = CEKIM[n]
    kim = "aerial drone photograph" if tur == "drone" else "photograph taken at eye level from the street"
    return (f"Edit this exact image into a real, unretouched {kim} in Armutlu, Yalova, Turkey. This is an edit, not a "
            "new picture: do not move the camera, do not zoom, do not rotate, do not re-frame. Every building, tree, car "
            "and object stays at exactly the same position, size and outline in the frame, so that the result can be "
            "laid exactly on top of the input; do not add, remove or merge any building and do not add floors. "
            f"{sahne} {BINA.replace('of the reference images', 'shown')} {AGAC} The houses of the town get fresh, clean plaster in warm cream and light ochre tones and "
            f"clean windows; nothing run-down. {ISIK} No CGI or toy-like look, no blur, no text, no watermark.")


def cipa_karesi(n):
    if n == 3:
        return 600                                          # denemeden hazır HQ kare, bölümü iyi temsil ediyor
    a, b = bolumler.BOLUM[n - 1]
    return (a + b) // 2


if __name__ == "__main__":
    n = int(sys.argv[1])
    print(json.dumps({"kare": cipa_karesi(n), "cipa": cipa(n), "kling": kling(n)}, ensure_ascii=False, indent=1))
