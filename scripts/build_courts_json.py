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
_ms = html.index("const MAP_STYLE = [")
MAP_STYLE = html[_ms + len("const MAP_STYLE = "):html.index("\n];", _ms) + 2]
_ls = html.index("const LANDMARKS = [")
LANDMARKS = json.loads(subprocess.run(["node", "-e", "process.stdout.write(JSON.stringify(" + html[_ls + len("const LANDMARKS = "):html.index("\n];", _ls) + 2] + "))"],
                                      capture_output=True, text=True, check=True).stdout)
GMAPS_KEY = re.search(r"const GMAPS_KEY = '([^']+)'", html)[1]   # domain-restricted browser key, same as index.html


SURF = {"c": "грунт", "h": "хард", "x": ""}
KIND = {"o": "на улице", "r": "под навесом", "i": "в зале", "d": "под куполом"}
BK = {"playon": "PlayOn", "playsport": "PlaySport", "tg": "Telegram", "site": "Сайт", "ig": "Instagram",
      "training": "Запись на тренировки", "photos": "Фото кортов"}
DAYS = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"]
SCHEMA_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
CSS = """@font-face{font-family:'Golos Text';font-weight:400;font-display:swap;src:url(/fonts/golos-text-cyrillic-400-normal.woff2) format('woff2')}
@font-face{font-family:'Golos Text';font-weight:600;font-display:swap;src:url(/fonts/golos-text-cyrillic-600-normal.woff2) format('woff2')}
@font-face{font-family:'Literata';font-display:swap;src:url(/fonts/literata-cyrillic-opsz-normal.woff2) format('woff2')}
:root{--ink:#111;--muted:#4F4F4F;--line:#E4E4E0;--soft:#F4F4F0;--ball:#DCEB4C;--court:#1E4D3A;--r-img:16px;--r-inner:12px}
*{box-sizing:border-box}body{margin:0;font:400 16px/1.5 'Golos Text',-apple-system,sans-serif;color:var(--ink);background:#fff}
main{max-width:1240px;margin:0 auto;padding:20px 20px 64px}main.narrow{max-width:880px}a{color:var(--court)}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding-bottom:16px;border-bottom:1px solid var(--ink)}
.top a{text-decoration:none;color:var(--ink);font-weight:600}.top .logo{font:500 28px/1 'Literata',Georgia,serif}
h1{font:500 clamp(36px,6vw,64px)/1.05 'Literata',Georgia,serif;margin:32px 0 12px;letter-spacing:-.01em}
h2{font:500 clamp(26px,3vw,36px)/1.15 'Literata',Georgia,serif;margin:48px 0 12px}
h3{font:500 22px/1.2 'Literata',Georgia,serif;margin:0 0 6px}h3 a{color:var(--ink);text-decoration:none}
.lead{font-size:18px;color:var(--muted);margin:0 0 24px;max-width:760px}
.ph{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:var(--r-img);background:var(--soft)}
dl{display:grid;grid-template-columns:minmax(120px,max-content) 1fr;gap:8px 20px;margin:20px 0}dt{color:var(--muted)}dd{margin:0}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:8px 18px;border-radius:999px;background:var(--ball);color:var(--ink);font-weight:600;text-decoration:none}
.btn:hover{background:#D0E03A}
.map{height:560px;border-radius:var(--r-img);background:var(--soft);z-index:0}
.lm{position:absolute;width:28px;height:28px;margin:-14px 0 0 -14px}.lm img{width:100%;height:100%;object-fit:cover;border:2px solid #fff;border-radius:50%;box-shadow:0 1px 4px #0004}
.lm span{position:absolute;left:50%;bottom:calc(100% + 3px);transform:translateX(-50%);font:600 13px 'Golos Text',sans-serif;white-space:nowrap;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;opacity:0;transition:opacity .15s}
.lm:hover span,.map.zoomed .lm span{opacity:1}.lm[hidden]{display:none}
.court-marker{background:none;border:0}.court-dot{display:block;width:100%;height:100%;border:2px solid #fff;border-radius:50%;background:var(--c);box-shadow:0 1px 4px #0005}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:12px 0 0;color:var(--muted);font-size:14px}.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.grid{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:40px 32px}
.grid li{display:grid;align-content:start;gap:8px}.grid .ph{margin-bottom:8px}.grid p{margin:0;color:var(--muted)}.grid .meta{color:var(--ink)}
.grid .ph.none{display:block;background:var(--soft) url(/img/ball.png) center/40px no-repeat}
.grid a.card{display:block;color:inherit;text-decoration:none}.grid a.card:hover h3{color:var(--court)}
.leaflet-popup-content{font:600 15px/1.35 'Golos Text',sans-serif;margin:10px 14px}.leaflet-popup-content a{color:var(--court)}
.note{color:var(--muted);font-size:14px}
.gal{position:relative}.gal figure{margin:0}.gal figure[hidden]{display:none}.gal figcaption{margin-top:8px;color:var(--muted)}
.gal .nav{position:absolute;top:calc(50% - 40px);width:44px;height:44px;border:0;border-radius:50%;background:#fffd;color:var(--ink);font:400 26px/1 'Golos Text',sans-serif;cursor:pointer;box-shadow:0 1px 6px #0003}
.gal .nav:hover{background:#fff}.gal .prev{left:12px}.gal .next{right:12px}
.thumbs{display:flex;gap:8px;margin:12px 0 0;padding:0;list-style:none;overflow-x:auto}
.thumbs button{flex:none;width:112px;padding:0;border:2px solid transparent;border-radius:var(--r-inner);background:none;cursor:pointer;overflow:hidden}
.thumbs button[aria-current="true"]{border-color:var(--ink)}.thumbs img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover}
.cfilt{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}
.cfilt button{display:inline-flex;align-items:center;gap:8px;height:40px;padding:0 16px;border:0;border-radius:999px;background:var(--soft);color:var(--ink);font:600 16px/1 'Golos Text',sans-serif;cursor:pointer}
.cfilt button:hover{background:var(--line)}.cfilt button[aria-pressed="true"]{background:var(--ink);color:#fff}
.cfilt i{width:10px;height:10px;border-radius:50%}.cfilt i.h{background:#2F6DB5}.cfilt i.c{background:#C2683A}.cfilt small{font:500 14px/1 'Golos Text',sans-serif;opacity:.6}
.grid li[hidden]{display:none}
@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.grid{grid-template-columns:1fr}.map{height:420px}dl{grid-template-columns:1fr;gap:2px}dd{margin-bottom:8px}}"""


def ru_plural(n, one, few, many):
    n = abs(n) % 100
    if 11 <= n <= 14:
        return many
    return {1: one, 2: few, 3: few, 4: few}.get(n % 10, many)


def esc(x):
    return escape(str(x or ""), quote=True)


def gallery_items(c):
    out, seen = [], set()
    for t in c.get("t", []):
        if len(t) > 2 and t[2] and t[2] not in seen and (ROOT / t[2]).exists():
            seen.add(t[2])
            label = (t[3][0] if len(t) > 3 and t[3] else "") or \
                " ".join(x for x in [SURF.get(t[0], ""), KIND.get(t[1], "")] if x).capitalize()
            out.append((t[2], label))
    if c.get("img") and c["img"] not in seen and (ROOT / c["img"]).exists():
        out.append((c["img"], "Общий вид"))
    return out


GALLERY_JS = """<script>
(() => {
  const g = document.querySelector('.gal'); if (!g) return;
  const figs = g.querySelectorAll('figure'), th = document.querySelectorAll('.thumbs button');
  let cur = 0;
  const show = i => { cur = (i + figs.length) % figs.length;
    figs.forEach((f, k) => f.hidden = k !== cur); th.forEach((b, k) => b.setAttribute('aria-current', k === cur)); };
  g.querySelector('.prev')?.addEventListener('click', () => show(cur - 1));
  g.querySelector('.next')?.addEventListener('click', () => show(cur + 1));
  th.forEach((b, k) => b.addEventListener('click', () => show(k)));
  document.addEventListener('keydown', e => {
    if (e.target.closest('input,textarea')) return;
    if (e.key === 'ArrowLeft') show(cur - 1); else if (e.key === 'ArrowRight') show(cur + 1);
  });
})();
</script>"""


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


TOP = '<div class="top"><a class="logo" href="/">Tennis Daily</a><a href="/korty/">Все корты Ташкента</a></div>'


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
        rows.append(("Как добраться", f'<a href="https://yandex.uz/maps/?rtext=~{ll[0]},{ll[1]}&rtt=auto" rel="noopener">Маршрут в Яндекс Картах</a>'
                                      f' · <a href="https://t.me/tennisdaily_uz_bot?start=court_{cid}_ru" rel="noopener">Отправить локацию в Telegram</a>'))
    dl = "".join(f"<dt>{k}</dt><dd>{v if k in ('Цена', 'Телефон', 'Бронь и связь', 'Как добраться') else esc(v)}</dd>" for k, v in rows)
    items = gallery_items(c)
    if len(items) > 1:
        figs = "".join(f'<figure{" hidden" if i else ""}><img class="ph" src="/{src}" alt="Теннисный корт «{esc(name)}», Ташкент: {esc(lab.lower())}"'
                       f'{" loading=\"lazy\"" if i else ""}><figcaption>{esc(lab)} · {i + 1} из {len(items)}</figcaption></figure>'
                       for i, (src, lab) in enumerate(items))
        thumbs = "".join(f'<li><button type="button" aria-label="{esc(lab)}" aria-current="{str(i == 0).lower()}"><img src="/{src}" alt="" loading="lazy"></button></li>'
                         for i, (src, lab) in enumerate(items))
        pic = (f'<div class="gal">{figs}<button type="button" class="nav prev" aria-label="Предыдущее фото">‹</button>'
               f'<button type="button" class="nav next" aria-label="Следующее фото">›</button></div><ul class="thumbs">{thumbs}</ul>')
    elif items:
        pic = f'<figure class="gal" style="margin:0"><img class="ph" src="/{items[0][0]}" alt="Теннисный корт «{esc(name)}», Ташкент"><figcaption>{esc(items[0][1])}</figcaption></figure>'
    else:
        pic = ""
    (folder / "index.html").write_text(head(title, desc, url, image) + court_jsonld(c, url, image) + f"""
</head>
<body>
<main class="narrow">
{TOP}
<h1>{esc(name)}</h1>
<p class="lead">{esc(desc)}</p>
{pic}
<dl>{dl}</dl>
<p><a class="btn" href="/?court={cid}">Открыть на карте Tennis Daily</a></p>
{GALLERY_JS if len(items) > 1 else ""}
<p class="note">Свободное время уточняйте по телефону или в онлайн-календаре брони. Данные о корте собирает редакция Tennis Daily; если что-то изменилось, напишите <a href="https://t.me/dandesdet">@dandesdet</a>.</p>
</main>
</body>
</html>
""", encoding="utf-8")


def landing_page(all_courts):
    url = f"{SITE}korty/"
    title = "Теннисные корты Ташкента — где поиграть и как забронировать · Tennis Daily"
    n = len(all_courts)
    places = f"{n} {ru_plural(n, 'теннисный клуб и площадка', 'теннисных клуба и площадки', 'теннисных клубов и площадок')}"
    desc = (f"{places} Ташкента на карте: грунт и хард, залы и улица. "
            "Часы работы, цены, телефоны и ссылки на онлайн-бронь.")
    items, pts, F = [], [], []
    for c in all_courts:
        photos = photos_of(c)
        img = (f'<img class="ph" src="/{photos[0]}" alt="Теннисный корт «{esc(c.get("ru"))}», Ташкент" loading="lazy">'
               if photos else '<span class="ph none"></span>')
        meta = " · ".join(x for x in [types_text(c), hours_text(c)] if x)
        meta = meta[:1].upper() + meta[1:]
        links = booking_links(c)
        bk = " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(n)}</a>' for u, n in links)
        tel = f'<a href="tel:{esc(c["tel"])}">{esc(c["tel"])}</a>' if c.get("tel") else ""
        contact = " · ".join(x for x in [tel, bk] if x)
        items.append(f'<li data-id="{c["id"]}"><a class="card" href="/court/{c["id"]}/">{img}<h3>{esc(c.get("ru"))}</h3></a>'
                     f'<p>{esc(c.get("dRu"))}</p>' + (f'<p class="meta">{esc(meta)}</p>' if meta else "") +
                     (f"<p>{contact}</p>" if contact else "") + "</li>")
        ll = c.get("ll") or []
        if len(ll) == 2:
            surf = {t[0] for t in c.get("t", [])} - {"x"}
            color = "#2F6DB5" if surf == {"h"} else "#C2683A" if surf == {"c"} else "#1E4D3A"
            pts.append({"id": c["id"], "n": c.get("ru"), "ll": ll, "c": color, "far": bool(c.get("far"))})
        F.append({"id": c["id"], "t": sorted({t[0] + (t[1] or "") for t in c.get("t", [])}), "h": c.get("h") or "",
                  "hT": c.get("hT") or {}, "off": c.get("offDays") or [], "st": c.get("st") or "", "full": c.get("full") or []})
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
<p class="lead">Где поиграть в теннис в Ташкенте: {places} — часы работы, цены, телефоны и ссылки на бронь. Все корты на одной карте — на <a href="/#courts">главной Tennis Daily</a>, там же фильтр «Открыто сейчас».</p>
<div class="cfilt" id="cfilt" role="group" aria-label="Фильтры кортов"></div>
<div class="map" id="map"></div>
<p class="legend"><span><i style="background:#2F6DB5"></i>хард</span><span><i style="background:#C2683A"></i>грунт</span><span><i style="background:#1E4D3A"></i>хард и грунт</span></p>
<h2>Как забронировать корт в Ташкенте</h2>
<p>Онлайн-бронь со свободным временем: <a href="https://playon.uz/korty-tashkent" rel="noopener">PlayOn</a> и <a href="https://booking.playsport.uz/ru/clubs/tennis-padel-city?sport=tennis" rel="noopener">PlaySport</a> (Пахтакор), а также боты <a href="https://t.me/tennis_plusbot" rel="noopener">@tennis_plusbot</a> и <a href="https://t.me/ace_club_courts_bot" rel="noopener">@ace_club_courts_bot</a>. В остальных клубах бронь по телефону — номера в списке ниже.</p>
<h2>Все корты</h2>
<ul class="grid">{"".join(items)}</ul>
<p class="note">Цены публикуем только с источником и датой проверки. Знаете ещё корт или видите ошибку — напишите <a href="https://t.me/dandesdet">@dandesdet</a>.</p>
</main>
<script>
(() => {{
  const P = {json.dumps(pts, ensure_ascii=False)};
  const F = {json.dumps(F, ensure_ascii=False)};
  const STYLE = {MAP_STYLE};
  // Same filters as the map on the main page.
  const TYPES = [['all','Все'],['now','Открыто сейчас'],['h','Весь хард'],['c','Весь грунт'],['hi','Хард в зале'],['hd','Хард под куполом'],
    ['ho','Хард на улице'],['hr','Хард под навесом'],['co','Грунт на улице'],['ci','Грунт в зале'],['24h','24/7']];
  const SEASON_OFF = ['co'];
  const span = t => {{ const m = (t || '').match(/^(\\d\\d):(\\d\\d)–(\\d\\d):(\\d\\d)$/); return m && [+m[1] * 60 + +m[2], +m[3] * 60 + +m[4]]; }};
  const openNow = c => {{
    if (c.st === 'off') return false;
    const d = new Date(Date.now() + 5 * 3600e3), now = d.getUTCHours() * 60 + d.getUTCMinutes();
    if (c.off.includes(d.getUTCDay())) return false;
    return (c.t.length ? c.t : ['']).some(k => {{
      if (SEASON_OFF.includes(k) || c.full.includes(k)) return false;
      const s = span(c.hT[k] || c.h); if (!s) return false;
      return s[1] > s[0] ? now >= s[0] && now < s[1] : now >= s[0] || now < s[1];
    }});
  }};
  const match = (c, f) => f === 'all' ? true : f === 'now' ? openNow(c) : f === '24h' ? c.h === '00:00–24:00' && c.st !== 'off'
    : c.t.some(k => k === f || k[0] === f && f.length === 1);
  let CF = 'all', markers = {{}};
  const apply = () => {{
    F.forEach(c => {{ const ok = match(c, CF); const li = document.querySelector(`.grid li[data-id="${{c.id}}"]`); if (li) li.hidden = !ok;
      if (markers[c.id]) markers[c.id].setVisible(ok); }});
    const el = document.getElementById('cfilt');
    el.innerHTML = TYPES.map(([k, n]) => {{ const cnt = F.filter(c => match(c, k)).length;
      return cnt || k === 'all' ? `<button type="button" data-k="${{k}}" aria-pressed="${{k === CF}}">${{/^[hc]/.test(k) ? `<i class="${{k[0]}}"></i>` : ''}}${{n}} <small>${{cnt}}</small></button>` : ''; }}).join('');
    el.querySelectorAll('button').forEach(b => b.onclick = () => {{ CF = b.dataset.k; apply(); }});
  }};
  apply();
  setInterval(() => CF === 'now' && apply(), 60e3);
  window.initMap = () => {{
    const g = google.maps;
    const map = new g.Map(document.getElementById('map'), {{center: {{lat: 41.33, lng: 69.28}}, zoom: 12, gestureHandling: 'cooperative',
      disableDefaultUI: true, zoomControl: true, clickableIcons: false, styles: STYLE}});
    const info = new g.InfoWindow(), bounds = new g.LatLngBounds();
    P.forEach(p => {{
      const m = new g.Marker({{position: {{lat: p.ll[0], lng: p.ll[1]}}, map, title: p.n,
        icon: {{path: g.SymbolPath.CIRCLE, scale: 6, fillColor: p.c, fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2}}}});
      markers[p.id] = m;
      m.addListener('click', () => {{ info.setContent(`<a href="/court/${{p.id}}/">${{p.n}}</a>`); info.open({{map, anchor: m}}); }});
      if (!p.far) bounds.extend(m.getPosition());
    }});
    const LM = {json.dumps([{"n": l["ru"], "ll": l["ll"], "img": "/" + l["img"], "z": l.get("minZoom", 0)} for l in LANDMARKS], ensure_ascii=False)};
    const lms = LM.map(l => {{
      const el = document.createElement('div'); el.className = 'lm'; el.innerHTML = `<img src="${{l.img}}" alt="" title="${{l.n}}"><span>${{l.n}}</span>`;
      const pos = new g.LatLng(...l.ll), ov = new g.OverlayView();
      ov.onAdd = () => ov.getPanes().overlayMouseTarget.append(el);
      ov.draw = () => {{ const pt = ov.getProjection().fromLatLngToDivPixel(pos); if (pt) {{ el.style.left = pt.x + 'px'; el.style.top = pt.y + 'px'; }} }};
      ov.onRemove = () => el.remove(); ov.setMap(map);
      return [el, l.z];
    }});
    const zoomed = () => {{ const z = map.getZoom(); lms.forEach(([el, mz]) => el.hidden = z < mz);
      document.getElementById('map').classList.toggle('zoomed', z >= 14); }};
    map.addListener('zoom_changed', zoomed);
    map.fitBounds(bounds, 30);
    zoomed(); apply();
  }};
  const sc = document.createElement('script');
  sc.src = 'https://maps.googleapis.com/maps/api/js?key={GMAPS_KEY}&callback=initMap&loading=async';
  sc.async = true; document.head.append(sc);
}})();
</script>
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
