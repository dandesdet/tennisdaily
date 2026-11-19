"""Build courts.json, court/<id>/ pages, the /korty/ landing page, sitemap.xml and robots.txt from COURTS in index.html.

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


SURF = {"c": "грунт", "h": "хард", "x": ""}
KIND = {"o": "на улице", "r": "под навесом", "i": "в зале", "d": "под куполом"}
BK = {"playon": "PlayOn", "playsport": "PlaySport", "tg": "Telegram", "site": "Сайт", "ig": "Instagram",
      "training": "Запись на тренировки", "photos": "Фото кортов"}
DAYS = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"]
SCHEMA_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
CSS = """@font-face{font-family:'Golos Text';font-weight:400;font-display:swap;src:url(/fonts/golos-text-cyrillic-400-normal.woff2) format('woff2')}
@font-face{font-family:'Golos Text';font-weight:600;font-display:swap;src:url(/fonts/golos-text-cyrillic-600-normal.woff2) format('woff2')}
@font-face{font-family:'Literata';font-display:swap;src:url(/fonts/literata-cyrillic-opsz-normal.woff2) format('woff2')}
:root{--ink:#111;--muted:#4F4F4F;--line:#E4E4E0;--soft:#F4F4F0;--ball:#DCEB4C;--court:#1E4D3A}
*{box-sizing:border-box}body{margin:0;font:400 16px/1.5 'Golos Text',-apple-system,sans-serif;color:var(--ink);background:#fff}
main{max-width:880px;margin:0 auto;padding:24px 20px 64px}a{color:var(--court)}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;font-weight:600}.top a{text-decoration:none;color:var(--ink)}
h1{font:500 clamp(32px,5vw,48px)/1.1 'Literata',Georgia,serif;margin:28px 0 12px}h2{font:500 26px/1.2 'Literata',Georgia,serif;margin:36px 0 10px}
h3{font-size:18px;margin:0 0 4px}.lead{font-size:18px;color:var(--muted);margin:0 0 20px}
.ph{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:16px;background:var(--soft)}
dl{display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:8px 20px;margin:20px 0}dt{color:var(--muted)}dd{margin:0}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:8px 18px;border-radius:999px;background:var(--ball);color:var(--ink);font-weight:600;text-decoration:none}
.list{list-style:none;padding:0;margin:0;display:grid;gap:0}.list li{display:grid;grid-template-columns:160px 1fr;gap:16px;padding:16px 0;border-top:1px solid var(--line)}
.list img{width:160px;aspect-ratio:16/9;object-fit:cover;border-radius:10px;background:var(--soft)}.list p{margin:2px 0;color:var(--muted)}
.note{color:var(--muted);font-size:14px}
@media(max-width:560px){.list li{grid-template-columns:1fr}.list img{width:100%}dl{grid-template-columns:1fr;gap:2px}dd{margin-bottom:8px}}"""


def esc(x):
    return escape(str(x or ""), quote=True)


def photos_of(c):
    return [t[2] for t in c.get("t", []) if len(t) > 2 and t[2] and (ROOT / t[2]).exists()] + \
           ([c["img"]] if c.get("img") and (ROOT / c["img"]).exists() else [])


def types_text(c):
    counts = c.get("counts") or {}
    seen, out = set(), []
    for t in c.get("t", []):
        key = t[0] + (t[1] or "")
        if key in seen:
            continue
        seen.add(key)
        label = " ".join(x for x in [SURF.get(t[0], ""), KIND.get(t[1], "")] if x) or "корт"
        n = counts.get(key)
        out.append(f"{label}: {n}" if n else label)
    return ", ".join(out)


def hours_text(c):
    if c.get("st") == "off":
        return c.get("stRu") or "закрыт"
    h = c.get("h") or ""
    if not h and c.get("hT"):
        h = next(iter(c["hT"].values()))
    if not h:
        return ""
    if h == "00:00–24:00":
        h = "круглосуточно"
    off = c.get("offDays") or []
    return h + (f", выходной: {', '.join(DAYS[d] for d in off)}" if off else "")


def price_lines(c):
    pT = c.get("pT") or {}
    src = pT.get("src", [""])[0]
    out = []
    for k, v in pT.items():
        if k == "src":
            continue
        label = " ".join(x for x in [SURF.get(k[0], ""), KIND.get(k[1:], "")] if x)
        out.append(f"{label.capitalize()}: {v[0]}" if label else v[0])
    return out, src


def booking_links(c):
    out = []
    for b in c.get("bk", []):
        u = b.get("u", "")
        if not u.startswith("http"):
            continue
        name = b.get("t") if b.get("t") and b.get("k") in ("tg", "ig") else BK.get(b.get("k")) or b.get("t") or \
            ("@" + u.rsplit("/", 1)[-1] if "t.me/" in u else u.split("/")[2].removeprefix("www."))
        out.append((u, name))
    return out


def court_jsonld(c, url, image):
    d = {"@context": "https://schema.org", "@type": "SportsActivityLocation", "name": c.get("ru"),
         "description": c.get("dRu"), "url": url, "sport": "Tennis",
         "address": {"@type": "PostalAddress", "addressLocality": "Ташкент", "addressCountry": "UZ"}}
    ll = c.get("ll") or []
    if len(ll) == 2:
        d["geo"] = {"@type": "GeoCoordinates", "latitude": ll[0], "longitude": ll[1]}
    if c.get("tel"):
        d["telephone"] = c["tel"]
    if image:
        d["image"] = image
    m = re.fullmatch(r"(\d\d:\d\d)–(\d\d:\d\d)", c.get("h") or "")
    if m and c.get("st") != "off":
        days = [SCHEMA_DAYS[i] for i in range(7) if i not in (c.get("offDays") or [])]
        d["openingHoursSpecification"] = [{"@type": "OpeningHoursSpecification", "dayOfWeek": days,
                                           "opens": m[1], "closes": "23:59" if m[2] in ("24:00", "00:00") else m[2]}]
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"


def head(title, desc, url, image):
    img = (f'<meta property="og:image" content="{image}">\n<meta property="og:image:width" content="1200">\n'
           f'<meta property="og:image:height" content="630">\n<meta name="twitter:card" content="summary_large_image">\n') if image else ""
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Tennis Daily">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
{img}<link rel="canonical" href="{url}">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<style>{CSS}</style>
"""


TOP = '<div class="top"><a href="/">Tennis Daily</a><a href="/korty/">Все корты Ташкента</a></div>'


def court_page(c):
    """Static, indexable court page (RU). It also serves as the share link for the court card."""
    cid = c["id"]
    folder = ROOT / "court" / cid
    folder.mkdir(parents=True, exist_ok=True)
    photos = photos_of(c)
    image = ""
    if photos:
        with Image.open(ROOT / photos[0]) as im:
            ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"), (1200, 630)).save(folder / "preview.jpg", quality=82)
        image = f"{SITE}court/{cid}/preview.jpg"
    name = c.get("ru", cid)
    desc = c.get("dRu") or "Теннисный корт в Ташкенте: часы работы, бронь, как добраться."
    title = f"Теннисный корт «{name}» в Ташкенте — часы, цены, бронь · Tennis Daily"
    url = f"{SITE}court/{cid}/"
    rows = []
    if types_text(c):
        rows.append(("Корты", types_text(c).capitalize()))
    if hours_text(c):
        rows.append(("Часы работы", hours_text(c)))
    prices, src = price_lines(c)
    if prices:
        rows.append(("Цена", "<br>".join(esc(x) for x in prices) + (f'<br><span class="note">{esc(src)}</span>' if src else "")))
    if c.get("access"):
        rows.append(("Условия", esc(c["access"][0])))
    if c.get("tel"):
        rows.append(("Телефон", f'<a href="tel:{esc(c["tel"])}">{esc(c["tel"])}</a>'))
    links = booking_links(c)
    if links:
        rows.append(("Бронь и связь", " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(n)}</a>' for u, n in links)))
    ll = c.get("ll") or []
    if len(ll) == 2:
        rows.append(("Как добраться", f'<a href="https://yandex.uz/maps/?rtext=~{ll[0]},{ll[1]}&rtt=auto" rel="noopener">Маршрут в Яндекс Картах</a>'))
    dl = "".join(f"<dt>{k}</dt><dd>{v if k in ('Цена', 'Телефон', 'Бронь и связь', 'Как добраться') else esc(v)}</dd>" for k, v in rows)
    pic = f'<img class="ph" src="/{photos[0]}" alt="Теннисный корт «{esc(name)}», Ташкент">' if photos else ""
    (folder / "index.html").write_text(head(title, desc, url, image) + court_jsonld(c, url, image) + f"""
</head>
<body>
<main>
{TOP}
<h1>{esc(name)}</h1>
<p class="lead">{esc(desc)}</p>
{pic}
<dl>{dl}</dl>
<p><a class="btn" href="/?court={cid}">Открыть на карте Tennis Daily</a></p>
<p class="note">Свободное время уточняйте по телефону или в онлайн-календаре брони. Данные о корте собирает редакция Tennis Daily; если что-то изменилось, напишите <a href="https://t.me/dandesdet">@dandesdet</a>.</p>
</main>
</body>
</html>
""", encoding="utf-8")


def landing_page(all_courts):
    url = f"{SITE}korty/"
    title = "Теннисные корты Ташкента — где поиграть и как забронировать · Tennis Daily"
    desc = (f"{len(all_courts)} теннисных кортов Ташкента на карте: грунт и хард, залы и улица. "
            "Часы работы, цены, телефоны и ссылки на онлайн-бронь.")
    items = []
    for c in all_courts:
        photos = photos_of(c)
        img = f'<img src="/{photos[0]}" alt="" loading="lazy">' if photos else "<span></span>"
        meta = " · ".join(x for x in [types_text(c), hours_text(c)] if x)
        meta = meta[:1].upper() + meta[1:]
        links = booking_links(c)
        bk = " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(n)}</a>' for u, n in links)
        tel = f'<a href="tel:{esc(c["tel"])}">{esc(c["tel"])}</a>' if c.get("tel") else ""
        contact = " · ".join(x for x in [tel, bk] if x)
        items.append(f'<li>{img}<div><h3><a href="/court/{c["id"]}/">{esc(c.get("ru"))}</a></h3>'
                     f'<p>{esc(c.get("dRu"))}</p>' + (f"<p>{esc(meta)}</p>" if meta else "") +
                     (f"<p>{contact}</p>" if contact else "") + "</div></li>")
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "Теннисные корты Ташкента",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITE}court/{c['id']}/", "name": c.get("ru")}
                              for i, c in enumerate(all_courts)]}
    folder = ROOT / "korty"
    folder.mkdir(exist_ok=True)
    (folder / "index.html").write_text(head(title, desc, url, f"{SITE}img/og-site.jpg") +
        '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>" + f"""
</head>
<body>
<main>
{TOP}
<h1>Теннисные корты Ташкента</h1>
<p class="lead">Где поиграть в теннис в Ташкенте: {len(all_courts)} кортов с часами работы, ценами, телефонами и ссылками на бронь. Все корты на одной карте — на <a href="/#courts">главной Tennis Daily</a>, там же фильтр «Открыто сейчас».</p>
<h2>Как забронировать корт в Ташкенте</h2>
<p>Онлайн-бронь со свободным временем: <a href="https://playon.uz/korty-tashkent" rel="noopener">PlayOn</a> и <a href="https://booking.playsport.uz/ru/clubs/tennis-padel-city?sport=tennis" rel="noopener">PlaySport</a> (Пахтакор), а также боты <a href="https://t.me/tennis_plusbot" rel="noopener">@tennis_plusbot</a> и <a href="https://t.me/ace_club_courts_bot" rel="noopener">@ace_club_courts_bot</a>. В остальных клубах бронь по телефону — номера в списке ниже.</p>
<h2>Все корты</h2>
<ul class="list">{"".join(items)}</ul>
<p class="note">Цены публикуем только с источником и датой проверки. Знаете ещё корт или видите ошибку — напишите <a href="https://t.me/dandesdet">@dandesdet</a>.</p>
</main>
</body>
</html>
""", encoding="utf-8")


def write_sitemap(court_ids):
    urls = [SITE, f"{SITE}korty/"] + [f"{SITE}court/{i}/" for i in court_ids]
    body = "".join(f"<url><loc>{u}</loc></url>\n" for u in urls)
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + body + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")


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

landing_page([c for c in json.loads(raw)])
write_sitemap(sorted(seen))
out = ROOT / "courts.json"
out.write_text(json.dumps({"courts": courts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"Wrote {len(courts)} courts to {out.name} and {len(seen)} pages to court/")
