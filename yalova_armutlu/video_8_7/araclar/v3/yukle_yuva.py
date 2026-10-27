# Önceden alınmış imzalı yükleme yuvasına dosya yükler: python3 yukle_yuva.py YUVA_ADI YEREL_DOSYA -> media_id yazar
import json, subprocess, sys
y = json.load(open("yuvalar.json"))[sys.argv[1]]
r = subprocess.run(["curl", "-sS", "-X", "PUT", "-H", f"Content-Type: {y['ct']}", "-H", "If-None-Match: *",
                    "--data-binary", "@" + sys.argv[2], y["url"], "-o", "/dev/null", "-w", "%{http_code}"],
                   capture_output=True, text=True)
print(sys.argv[2], "->", y["media_id"], r.stdout, r.stderr[:100])
