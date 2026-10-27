# Vaziyet planı verisini (parseller, 8+9 blok konturları, kıyı) JSON'a döker; Blender içinde çalışır.
import json, os, runpy, sys
sys.argv = [sys.argv[0], "--", "--sol", "8", "--sag", "9"]
ns = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "yalova_armutlu_16blok.py"), run_name="plan_dok")
bl = ns["yerlesim"]()
out = {"P7104": ns["P7104"], "P7105": ns["P7105"], "KIYI": ns["KIYI"],
       "SAHIL_YOLU": ns.get("SAHIL_YOLU"), "bloklar": bl,
       "kontur": {k: ns["_kontur"](t, True) for k, t in ns["BLOK_TIPLERI"].items()}}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan.json"), "w"), default=list)
print("plan tamam", len(bl))
