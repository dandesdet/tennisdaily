#!/usr/bin/env python3
"""Аватарки призёров: заменяет инициалы <b class="a" title="Имя Фамилия"> на фото из «Круга общения» (tennis-base).

Запуск из корня репозитория:
  python3 scripts/avatars.py            # показать, что найдено, ничего не менять
  python3 scripts/avatars.py --write    # сохранить av/<slug>.webp и вставить их в index.html

Нужны Pillow и opencv-python (поиск лица). База — ~/Downloads/tennis-base или TENNIS_BASE.
Человек и фото выбираются так же, как в people.html (localhost:8766/people.html):
- люди: data.js + игроки PlayOn + добавленные вручную, с правками из store.js (имя, склейки, удалённые);
- имя: полное совпадение с именем в базе или с привязанным игроком PlayOn; ручные привязки «фамилия и.» из списков;
- фото: своё из store_photos.js → выбранное главное → обложка бота → Telegram → другие фото профиля.
Решения по сайту — в av/people.json: {"Имя Фамилия": "<id из базы>"} или "skip" (чужое фото, ребёнок, нет лица).
После --write открыть av/review.jpg и проверить каждое лицо глазами.
"""
import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BASE = Path(os.environ.get('TENNIS_BASE', Path.home() / 'Downloads' / 'tennis-base'))
SIZE = 192
HEAD, FILL = 1.4, 0.85  # как в tennis-base/face_crop.py: голова ≈ 1.4 высоты лица, занимает 85% кадра

CYR = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюяўқғҳ',
               'a b v g d e yo j z i y k l m n o p r s t u f x s ch sh sh _ i _ e yu ya o q g h'.split()))


def latin(s):
    return ''.join(CYR.get(c, c) for c in s.lower()).replace('_', '')


def key(name):
    s = re.sub(r'[^a-z ]', '', latin(name))
    for a, b in (('kh', 'x'), ('dj', 'j'), ('zh', 'j'), ('ts', 's'), ('ye', 'e'), ('yo', 'o'),
                 ('yu', 'u'), ('ya', 'a'), ('iy', 'i'), ('y', 'i'), ('ii', 'i')):
        s = s.replace(a, b)
    return ' '.join(sorted(s.split()))


def js_value(file, var):
    t = (BASE / file).read_text(encoding='utf-8')
    i = t.index(f'window.{var}')
    t = t[t.index('=', i) + 1:].lstrip()
    return json.JSONDecoder().raw_decode(t)[0]


def load_base():
    store = js_value('store.js', 'TG_STORE')
    edits = store.get('circle.edits', {})
    people = js_value('data.js', 'TG_DATA') + js_value('playon_people.js', 'TG_PLAYON_PEOPLE') \
        + store.get('circle.added', [])
    by_id = {str(p['id']): p for p in people}
    names = {}
    for p in people:
        pid = str(p['id'])
        ed = edits.get(pid, {})
        if ed.get('deleted') and not ed.get('mergedInto'):
            continue
        full = ed.get('name') or f"{p.get('first', '')} {p.get('last', '')}".strip()
        po = ed.get('po') or p.get('po') or {}
        for n in {full, po.get('name', '')} - {''}:
            names.setdefault(key(n), set()).add(pid)
    picks = store.get('circle.listpicks', {})
    return by_id, edits, names, picks, js_value('store_photos.js', 'TG_STORE_PHOTOS'), js_value('covers.js', 'TG_COVERS')


def alive(pid, edits):
    for _ in range(10):  # склеенные дубли ведут к основной карточке
        nxt = edits.get(pid, {}).get('mergedInto')
        if not nxt:
            break
        pid = str(nxt)
    return pid


def sources(pid, by_id, edits, own, covers):
    ed, p = edits.get(pid, {}), by_id.get(pid, {})
    for s in (own.get(pid), ed.get('photoMain'), covers.get(pid), p.get('photo'),
              *(ed.get('altPhotos') or []), ed.get('mergedPhoto')):
        if (isinstance(s, str) and s) or (isinstance(s, dict) and s.get('src')):
            yield s


def region(src):
    """Квадрат, который выбрали вручную в people.html: {src, x, y, s, w, h} в пикселях кадра w×h."""
    img = read(src['src'])
    if img is None:
        return None
    k = img.shape[1] / src.get('w', img.shape[1])
    x, y, side = (int(src[c] * k) for c in ('x', 'y', 's'))
    crop = img[max(0, y):y + side, max(0, x):x + side]
    return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).resize((SIZE, SIZE), Image.LANCZOS)


def read(src):
    if src.startswith('data:'):
        data = base64.b64decode(src.split(',', 1)[1])
    elif src.startswith('http'):
        data = urllib.request.urlopen(src, timeout=20).read()
    else:
        f = BASE / src.split('?')[0]
        if not f.exists():
            return None
        data = f.read_bytes()
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def face_crop(img):
    """Квадрат вокруг единственного лица. Возвращает (картинка | None, число лиц)."""
    h, w = img.shape[:2]
    best = (None, 0)
    # детектор путается на крупных планах: ищем на уменьшенном кадре, мелкие лица на фоне не считаем
    for long_side in (320, 640):
        k = min(1, long_side / max(w, h))
        sw, sh = int(w * k), int(h * k)
        det = cv2.FaceDetectorYN.create(str(BASE / 'face_detector.onnx'), '', (sw, sh), 0.8)
        _, faces = det.detect(cv2.resize(img, (sw, sh)))
        faces = [f[:4] / k for f in (faces if faces is not None else []) if f[3] >= 0.12 * min(sw, sh)]
        if len(faces) == 1:
            best = (faces[0], 1)
            break
        best = (None, max(best[1], len(faces)))
    if best[1] != 1:
        return best
    x, y, fw, fh = best[0]
    side = min(fh * HEAD / FILL, w, h)
    cx, cy = x + fw / 2, y + fh / 2 - fh * 0.12
    left = int(max(0, min(w - side, cx - side / 2)))
    top = int(max(0, min(h - side, cy - side / 2)))
    crop = img[top:top + int(side), left:left + int(side)]
    return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).resize((SIZE, SIZE), Image.LANCZOS), 1


def find(name, manual, names, picks, edits):
    m = manual.get(name, '')
    if m:
        return [] if m == 'skip' else [alive(m, edits)]
    ids = {alive(i, edits) for i in names.get(key(name), set())}
    if not ids:
        first, last = name.split()[0], name.split()[-1]
        for k in (f'{last} {first[0]}.', f'{last} {first[0]}'):
            if k.lower() in picks:
                ids = {alive(str(picks[k.lower()]), edits)}
                break
    return sorted(ids)


def main():
    write = '--write' in sys.argv
    manual_f = ROOT / 'av' / 'people.json'
    manual = json.loads(manual_f.read_text(encoding='utf-8')) if manual_f.exists() else {}
    by_id, edits, names, picks, own, covers = load_base()
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    have = {t: s for s, t in re.findall(r'<img class="a" src="(av/[^"]+)" alt="" title="([^"]+)"', html)}
    done, review = {}, []
    for name in sorted(set(re.findall(r'<b class="a" title="([^"]+)">', html))):
        if name in have:
            done[name] = have[name]
            print(f'ЕСТЬ      {name}: {have[name]}')
            continue
        if manual.get(name) == 'skip':
            print(f'ПРОПУСК   {name}: av/people.json')
            continue
        ids = find(name, manual, names, picks, edits)
        users = {(by_id.get(i, {}).get('username') or '').lower() for i in ids}
        same = len(ids) > 1 and len(users) == 1 and '' not in users  # нескленные дубли одного аккаунта
        if len(ids) != 1 and not same:
            print(f'НЕТ       {name}: ' + ('нет в базе' if not ids else
                  f'несколько: {", ".join(ids)} — уточните в av/people.json'))
            continue
        pid = '+'.join(ids)
        result, why = None, 'нет фото'
        for src in (s for i in ids for s in sources(i, by_id, edits, own, covers)):
            if isinstance(src, dict):  # ручной выбор — без детектора
                result = region(src)
                if result:
                    break
                continue
            try:
                img = read(src)
            except (OSError, ValueError) as e:  # сеть или битый файл — пробуем следующий источник
                why = f'не скачалось: {e}'
                continue
            if img is None:
                continue
            result, n = face_crop(img)
            if result:
                break
            why = 'лица нет' if n == 0 else f'лиц на фото: {n}'
        if not result:
            print(f'НЕТ ФОТО  {name} ({pid}): {why}')
            continue
        first, last = name.split()[0], name.split()[-1]
        path = f'av/{re.sub("[^a-z]", "", latin(last).replace("x", "kh"))}.webp'
        if (ROOT / path).exists():
            path = path.replace('.webp', f'-{re.sub("[^a-z]", "", latin(first).replace("x", "kh"))}.webp')
        print(f'НОВОЕ     {name} ({pid}) → {path}')
        done[name] = path
        review.append((name, result))
        if write:
            result.save(ROOT / path, 'WEBP', quality=86)
    if not write:
        return
    for name, path in done.items():
        html = re.sub(rf'<b class="a" title="{re.escape(name)}">[^<]*</b>',
                      f'<img class="a" src="{path}" alt="" title="{name}">', html)
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    if review:
        sheet = Image.new('RGB', (SIZE * len(review), SIZE), 'white')
        for i, (_, im) in enumerate(review):
            sheet.paste(im, (i * SIZE, 0))
        sheet.save(ROOT / 'av' / 'review.jpg', quality=85)
        print('Проверьте лица глазами: av/review.jpg (в гит не добавлять), порядок — как строки НОВОЕ')


if __name__ == '__main__':
    main()
