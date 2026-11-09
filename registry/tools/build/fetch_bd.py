"""Brčko District: fetch the Assembly's law register (skupstinabd.ba) into <src>. Private (never published).

    python -X utf8 fetch_bd.py index  --src DIR [--interval 0.6]   # the register index + every law's page (always re-read)
    python -X utf8 fetch_bd.py pdfs   --src DIR [--interval 0.6]   # every PDF the pages list (cached: read once)

Writes <src>/register.json: {law id: {"page", "title", "files": [{"name", "url", "issue": [year, n] | null}]}},
<src>/by-url/<sha256(url)> (raw bytes), <src>/requests.jsonl (one line per request). At most one request per
--interval seconds (default 0.6, under 2 a second). Stops on 403/429, two 5xx in a row, or a challenge page, writing
<src>/STOP with the reason.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests

UA = 'lexifina-watch/1.0 (+https://lexifina.com/watch; corpus@lexifina.com)'
BASE = 'https://skupstinabd.ba'
INDEX = BASE + '/index.php/ba/zakon.html'
ISSUE = re.compile(r'^\s*(\d+)\s*[A-Za-z]{0,3}\s*[- ]?\s*(\d{1,3})\s*-\s*(\d{2})(?!\d)')


def issue_of(name: str):
    m = ISSUE.match(name)
    if not m:
        return None
    y = int(m.group(3))
    return [2000 + y if y < 60 else 1900 + y, int(m.group(2))]


class Get:
    def __init__(self, src: Path, interval: float):
        self.src, self.iv, self.last, self.bad = src, interval, 0.0, 0
        self.s = requests.Session()
        self.s.headers['User-Agent'] = UA

    def path(self, url: str) -> Path:
        return self.src / 'by-url' / hashlib.sha256(url.encode()).hexdigest()

    def stop(self, why: str):
        (self.src / 'STOP').write_text(why + '\n', encoding='utf-8')
        raise SystemExit('stop: ' + why)

    def get(self, url: str, refresh: bool = False) -> Path | None:
        p = self.path(url)
        if p.exists() and not refresh:
            return p
        w = self.iv - (time.time() - self.last)
        if w > 0:
            time.sleep(w)
        try:
            r = self.s.get(url, timeout=90)
            code = r.status_code
        except requests.RequestException as e:
            code, r = 0, None
            err = str(e)[:200]
        self.last = time.time()
        with open(self.src / 'requests.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps({'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'url': url, 'code': code}) + '\n')
        if code in (403, 429):
            self.stop(f'{code} on {url}')
        if code == 0 or code >= 500:
            self.bad += 1
            if self.bad >= 2:
                self.stop(f'two failures in a row ({code}) on {url}')
            time.sleep(20)
            return self.get(url, refresh)
        self.bad = 0
        if code != 200:
            print('skip', code, url, flush=True)
            return None
        head = r.content[:4000].lower()
        if b'just a moment' in head or b'captcha' in head or b'cf-chl' in head:
            self.stop(f'challenge page on {url}')
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix('.part')
        tmp.write_bytes(r.content)
        tmp.replace(p)
        return p


def page_url(law_id: str) -> str:
    return 'https://skupstinabd.ba/index.php/ba/zakon.html?lang=ba&id=' + urllib.parse.quote(law_id, safe='/-')


def index(g: Get):
    t = g.get(INDEX, refresh=True).read_text(encoding='utf-8', errors='replace')
    ids = sorted(set(re.findall(r"zakon\.html\?lang=ba&id=([^']*)'", t)))
    if len(ids) < 150:
        g.stop(f'register index lists only {len(ids)} laws')
    reg = {}
    for i, law_id in enumerate(ids):
        url = page_url(law_id)
        p = g.get(url, refresh=True)
        if p is None:
            reg[law_id] = {'page': url, 'title': None, 'files': [], 'error': 'page not served'}
            continue
        h = p.read_text(encoding='utf-8', errors='replace')
        links = re.findall(r"href='(https://skupstinabd.ba/3-zakon/[^']*)'", h)
        title = re.search(r'<h3>\s*([^<]+?)\s*</h3>', h)
        reg[law_id] = {'page': url, 'title': title.group(1) if title else None,
                       'files': [{'name': l.rsplit('/', 1)[1], 'url': urllib.parse.quote(l, safe=':/'),
                                  'issue': issue_of(l.rsplit('/', 1)[1])} for l in links]}
        print(i + 1, len(ids), law_id, len(links), flush=True)
    (g.src / 'register.json').write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding='utf-8')
    st = {'register_read': time.strftime('%Y-%m-%d', time.gmtime()), 'laws': len(reg),
          'files': sum(len(v['files']) for v in reg.values())}
    (g.src / 'refresh-state.json').write_text(json.dumps(st, indent=1), encoding='utf-8')
    print(st)


def pdfs(g: Get):
    reg = json.loads((g.src / 'register.json').read_text(encoding='utf-8'))
    urls = [f['url'] for v in reg.values() for f in v['files']]
    for i, u in enumerate(urls):
        p = g.get(u)
        if i % 25 == 0:
            print(i, len(urls), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=['index', 'pdfs'])
    ap.add_argument('--src', required=True)
    ap.add_argument('--interval', type=float, default=0.6)
    a = ap.parse_args()
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass
    src = Path(a.src)
    src.mkdir(parents=True, exist_ok=True)
    (src / 'STOP').unlink(missing_ok=True)
    g = Get(src, a.interval)
    {'index': index, 'pdfs': pdfs}[a.what](g)


if __name__ == '__main__':
    main()
