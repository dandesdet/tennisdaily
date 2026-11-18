"""Build courts.json (id, names, coordinates) and court/<id>/ share pages from COURTS in index.html.

The Telegram location bot reads https://tennisdaily.uz/courts.json, so the site
stays the single source of court coordinates. Run after editing COURTS:
    python3 scripts/build_courts_json.py
Requires Node.js (used to evaluate the COURTS literal) and Pillow (preview images).
"""

import json
import re
import subprocess
from html import escape
from PIL import Image, ImageOps
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
start = html.index("const COURTS = [")
end = html.index("\n];", start) + 3
literal = html[start:end].replace("const COURTS =", "", 1).rstrip(";")

raw = subprocess.run(
    ["node", "-e", f"process.stdout.write(JSON.stringify({literal}))"],
    capture_output=True, text=True, check=True,
).stdout

SITE = "https://tennisdaily.uz/"


def court_page(c):
    """Static page with link preview; it forwards visitors to the site with the court card open."""
    cid = c["id"]
    folder = ROOT / "court" / cid
    folder.mkdir(parents=True, exist_ok=True)
    photos = [t[2] for t in c.get("t", []) if len(t) > 2 and t[2]] + ([c["img"]] if c.get("img") else [])
    image = ""
    for src in photos:
        path = ROOT / src
        if path.exists():
            with Image.open(path) as im:
                ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"), (1200, 630)).save(folder / "preview.jpg", quality=82)
            image = f"{SITE}court/{cid}/preview.jpg"
            break
    title = f"{c.get('ru', cid)} · теннисные корты Ташкента"
    desc = c.get("dRu") or "Корт в Ташкенте: часы работы, бронь, как добраться."
    url = f"{SITE}court/{cid}/"
    img_tags = (f'<meta property="og:image" content="{image}">\n<meta property="og:image:width" content="1200">\n'
                f'<meta property="og:image:height" content="630">\n<meta name="twitter:card" content="summary_large_image">\n') if image else ""
    (folder / "index.html").write_text(f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · Tennis Daily</title>
<meta name="description" content="{escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Tennis Daily">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{url}">
{img_tags}<link rel="canonical" href="{url}">
</head>
<body>
<h1>{escape(c.get('ru', cid))}</h1>
<p>{escape(desc)}</p>
<p><a id="court-link" href="../../?court={cid}">Открыть на Tennis Daily</a></p>
<script>location.replace(document.getElementById('court-link').href);</script>
</body>
</html>
""", encoding="utf-8")


courts, seen = [], set()
for c in json.loads(raw):
    cid = c.get("id", "")
    if not re.fullmatch(r"[a-z0-9-]{1,40}", cid):
        raise SystemExit(f"Court without a valid id: {c.get('ru')}")
    if cid in seen:
        raise SystemExit(f"Duplicate court id: {cid}")
    seen.add(cid)
    court_page(c)
    ll = c.get("ll") or []
    if not (len(ll) == 2 and -90 <= ll[0] <= 90 and -180 <= ll[1] <= 180):
        continue  # no usable coordinates: the bot will not offer this court
    courts.append({
        "id": cid,
        "name": {"ru": c.get("ru", ""), "uz": c.get("uz") or c.get("ru", ""), "en": c.get("en") or c.get("ru", "")},
        "lat": ll[0],
        "lon": ll[1],
    })

out = ROOT / "courts.json"
out.write_text(json.dumps({"courts": courts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"Wrote {len(courts)} courts to {out.name} and {len(seen)} pages to court/")
