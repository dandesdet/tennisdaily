#!/usr/bin/env python3
"""Аватарки призёров: заменяет инициалы <b class="a" title="Имя Фамилия"> на фото из базы tennis-base.

Запуск из корня репозитория:
  python3 scripts/avatars.py            # показать, что найдено, ничего не менять
  python3 scripts/avatars.py --write    # сохранить av/<slug>.webp и вставить их в index.html

Нужны Pillow и opencv-python (поиск лица). База — ~/Downloads/tennis-base или TENNIS_BASE.
Источники по порядку: photos_remote/cover_<id>.jpg, photos/<id>.jpg (Telegram), аватар PlayOn.
Имя должно совпасть полностью (кириллица и латиница сводятся к одному виду). Ручные решения —
в av/people.json: {"Имя Фамилия": "tg:<id>"} — кто это в Telegram, или "skip" — оставить инициалы
(чужое фото, ребёнок, нет лица). После --write открыть av/review.jpg и проверить каждое лицо глазами.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

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


def load_people():
    tg = json.loads((BASE / 'people.json').read_text(encoding='utf-8'))
    js = (BASE / 'playon_people.js').read_text(encoding='utf-8')
    po = json.loads(js[js.index('['):js.rindex(']') + 1])
    by = {}
    for pid, p in tg.items():
        by.setdefault(key(f"{p.get('first', '')} {p.get('last', '')}"), []).append(('tg', pid, p))
    for p in po:
        by.setdefault(key(p['po']['name']), []).append(('po', p['id'], p))
    return tg, by


def sources(kind, pid, p):
    if kind == 'tg':
        for f in (BASE / 'photos_remote' / f'cover_{pid}.jpg', BASE / 'photos' / f'{pid}.jpg'):
            if f.exists():
                yield str(f)
    elif p.get('photo', '').startswith('http'):
        yield p['photo']


def read(src):
    if src.startswith('http'):
        data = urllib.request.urlopen(src, timeout=20).read()
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    return cv2.imread(src)


def face_crop(img):
    """Квадрат вокруг единственного лица. Возвращает (картинка | None, число лиц)."""
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(str(BASE / 'face_detector.onnx'), '', (w, h), 0.9)
    _, faces = det.detect(img)
    n = 0 if faces is None else len(faces)
    if n != 1:
        return None, n
    x, y, fw, fh = faces[0][:4]
    side = min(fh * HEAD / FILL, w, h)
    cx, cy = x + fw / 2, y + fh / 2 - fh * 0.12
    left = int(max(0, min(w - side, cx - side / 2)))
    top = int(max(0, min(h - side, cy - side / 2)))
    crop = img[top:top + int(side), left:left + int(side)]
    return Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).resize((SIZE, SIZE), Image.LANCZOS), 1


def main():
    write = '--write' in sys.argv
    manual_f = ROOT / 'av' / 'people.json'
    manual = json.loads(manual_f.read_text(encoding='utf-8')) if manual_f.exists() else {}
    tg, by = load_people()
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    have = {t: s for s, t in re.findall(r'<img class="a" src="(av/[^"]+)" alt="" title="([^"]+)"', html)}
    done, review = {}, []
    for name in sorted(set(re.findall(r'<b class="a" title="([^"]+)">', html))):
        if name in have:
            done[name] = have[name]
            print(f'ЕСТЬ      {name}: {have[name]}')
            continue
        m = manual.get(name, '')
        if m == 'skip':
            print(f'ПРОПУСК   {name}: av/people.json')
            continue
        cands = [('tg', m[3:], tg[m[3:]])] if m.startswith('tg:') else by.get(key(name), [])
        if len(cands) != 1:
            print(f'НЕТ       {name}: ' + ('нет в базе' if not cands else
                  'несколько: ' + ', '.join(f'{k}:{i}' for k, i, _ in cands) + ' — уточните в av/people.json'))
            continue
        kind, pid, p = cands[0]
        result, why = None, 'нет фото'
        for src in sources(kind, pid, p):
            try:
                img = read(src)
            except OSError as e:  # сеть или битый файл — пробуем следующий источник
                why = f'не скачалось: {e}'
                continue
            if img is None:
                continue
            result, n = face_crop(img)
            if result:
                break
            why = 'лица нет' if n == 0 else f'лиц на фото: {n}'
        if not result:
            print(f'НЕТ ФОТО  {name} ({kind}:{pid}): {why}')
            continue
        first, last = name.split()[0], name.split()[-1]
        path = f'av/{re.sub("[^a-z]", "", latin(last).replace("x", "kh"))}.webp'
        if (ROOT / path).exists():
            path = path.replace('.webp', f'-{re.sub("[^a-z]", "", latin(first).replace("x", "kh"))}.webp')
        print(f'НОВОЕ     {name} ({kind}:{pid}) → {path}')
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
        sheet = Image.new('RGB', (SIZE * len(review), SIZE + 28), 'white')
        d = ImageDraw.Draw(sheet)
        for i, (name, im) in enumerate(review):
            sheet.paste(im, (i * SIZE, 0))
            d.text((i * SIZE + 6, SIZE + 8), name, fill='black')
        sheet.save(ROOT / 'av' / 'review.jpg', quality=85)
        print('Проверьте лица глазами: av/review.jpg (в гит не добавлять)')


if __name__ == '__main__':
    main()
