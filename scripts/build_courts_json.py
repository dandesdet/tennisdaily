"""Build courts.json (id, names, coordinates) from COURTS in index.html.

The Telegram location bot reads https://tennisdaily.uz/courts.json, so the site
stays the single source of court coordinates. Run after editing COURTS:
    python3 scripts/build_courts_json.py
Requires Node.js (used to evaluate the COURTS literal).
"""

import json
import re
import subprocess
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

courts, seen = [], set()
for c in json.loads(raw):
    cid = c.get("id", "")
    if not re.fullmatch(r"[a-z0-9-]{1,40}", cid):
        raise SystemExit(f"Court without a valid id: {c.get('ru')}")
    if cid in seen:
        raise SystemExit(f"Duplicate court id: {cid}")
    seen.add(cid)
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
print(f"Wrote {len(courts)} courts to {out.name}")
