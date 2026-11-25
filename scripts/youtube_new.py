#!/usr/bin/env python3
"""Ролики YouTube-канала @dandesdet, которых ещё нет в index.html.

Запуск из корня репозитория:  python3 scripts/youtube_new.py [--since 2026-10-01]
Нужен yt-dlp. Печатает дату, ID, формат (shorts / wide) и название.
Пустой вывод — новых роликов нет.
Затем проверяет все обложки i.ytimg.com в index.html: битая печатается как BROKEN.
Вертикальной обложки oar2.jpg нет у горизонтальных роликов — берите maxresdefault.jpg.
"""
import argparse
import re
import urllib.error
import urllib.request
import subprocess
import sys

CHANNEL = 'https://www.youtube.com/@dandesdet'


def ids(tab):
    out = subprocess.run(['yt-dlp', '--flat-playlist', '--print', '%(id)s', f'{CHANNEL}/{tab}'],
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.split() if line]


def meta(vid):
    out = subprocess.run(['yt-dlp', '--skip-download', '--print', '%(upload_date)s\t%(title)s',
                          f'https://www.youtube.com/watch?v={vid}'],
                         capture_output=True, text=True).stdout.strip()
    return out.split('\t', 1) if '\t' in out else ('', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--since', default='2026-10-01', help='не старше этой даты (ГГГГ-ММ-ДД)')
    since = ap.parse_args().since.replace('-', '')
    site = open('index.html', encoding='utf-8').read()
    for tab, kind in (('shorts', 'shorts'), ('videos', 'wide')):
        # вкладки идут от новых к старым: останавливаемся на первом ролике старше --since
        for vid in ids(tab):
            if vid in site:
                continue
            date, title = meta(vid)
            if date and date < since:
                break
            print(f'{date}\t{vid}\t{kind}\t{title}')
    broken = 0
    for url in sorted(set(re.findall(r'https://i\.ytimg\.com/vi/[\w-]+/\w+\.jpg', site))):
        try:
            urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=15)
        except urllib.error.URLError:
            print(f'BROKEN\t{url}')
            broken += 1
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main())
