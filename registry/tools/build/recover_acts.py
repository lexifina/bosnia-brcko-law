"""Recover the acts a repository already publishes as a corpus part, read back from main (2026-11-09).

An append's documentation commit (data/acts.json, ACTS.md, paths) lists only the corpus it was given, so a corpus that
holds only new acts would drop the published ones from the indexes. This part holds every published act: its versions
from data/versions.json (and registry/data/versions.json), each version's units read from main at the commit whose
In-force trailer is that version's day (labels from the act's README table), and its laws from data/laws.csv.
append.py then reads them back against main as unchanged (same text), so nothing is appended for them.

    python -X utf8 recover_acts.py <repo> <out part.json> [--label slug=label ...] [--extra extra.json]

--extra: {slug: {field: value}} merged into recovered acts (e.g. a label "amended, not consolidated", amended_by).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
from pathlib import Path


def git(repo, *a):
    return subprocess.run(['git', *a], cwd=repo, capture_output=True, text=True, encoding='utf-8', check=True).stdout


_CAT = {}


def show(repo, spec):
    """One long-lived `git cat-file --batch` per repository (process start is slow on Windows)."""
    p = _CAT.get(str(repo))
    if p is None:
        p = _CAT[str(repo)] = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=repo, stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE)
    p.stdin.write(spec.encode('utf-8') + b'\n')
    p.stdin.flush()
    head = p.stdout.readline().decode()
    if head.endswith('missing\n') or len(head.split()) < 3:
        return None
    data = p.stdout.read(int(head.split()[2]))
    p.stdout.read(1)
    return data.decode('utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('repo')
    ap.add_argument('out')
    ap.add_argument('--extra')
    a = ap.parse_args()
    repo = Path(a.repo)
    extra = json.loads(Path(a.extra).read_text(encoding='utf-8')) if a.extra else {}
    acts, laws = [], {}
    for prefix in ('', 'registry/'):
        vj = show(repo, f'main:{prefix}data/versions.json')
        if not vj:
            continue
        lc = show(repo, f'main:{prefix}data/laws.csv') or ''
        for row in csv.DictReader(io.StringIO(lc)):
            laws.setdefault(row['key'], {'label': row['label'], 'title': row['title'], 'kind': row['kind'] or 'law',
                                         'enacted': row['enacted'] or None, 'published': row['published'] or None,
                                         'url': row['url'] or None, 'temporary_until': None, 'restores': None,
                                         'note': None})
        for act in json.loads(vj)['acts']:
            folder = act.get('path') or act['slug']
            if not git(repo, 'ls-tree', '--name-only', 'main', folder + '/').strip():
                continue  # withdrawn
            log = git(repo, 'log', '--first-parent', 'main', '--format=%H%x09%(trailers:key=In-force,valueonly,separator=)%x09%(trailers:key=Law,valueonly,separator=)', '--', folder)
            by_day = {}
            for ln in log.splitlines():
                h, d, law = (ln.split('\t') + ['', ''])[:3]
                if d.strip():
                    by_day.setdefault(d.strip()[:10], (h, law.strip()))  # newest first: the last commit of the day
            readme = show(repo, f'main:{folder}/README.md') or ''
            labels = {m.group(2): m.group(1) for m in re.finditer(r'^\| (.+?) \| \[([^\]]+)\.md\]', readme, re.M)}
            versions = []
            first_law = None
            for v in act['versions']:
                h, law = by_day[v['from']]
                names = [n for n in git(repo, 'ls-tree', '--name-only', h, folder + '/').split('\n') if n.endswith('.md')]
                units = {}
                for n in sorted(names):
                    key = n.rsplit('/', 1)[1][:-3]
                    if key == 'README':
                        continue
                    units[key] = {'label': labels.get(key, key), 'kind': 'art' if key.startswith('clan-') else 'note',
                                  'text': show(repo, f'{h}:{n}')}
                versions.append({'from': v['from'], 'source_url': v.get('source_url'), 'sha256': v.get('sha256'),
                                 'units': units})
                if not versions[:-1]:
                    m = re.search(r'^Law: (.*)$', git(repo, 'log', '-1', '--format=%B', h), re.M)
                    if m and ' as enacted' in git(repo, 'log', '-1', '--format=%s', h):
                        first_law = next((k for k, l in laws.items() if l['label'] == m.group(1).strip()), None)
            rec = {'slug': act['slug'], 'short': act.get('short', ''), 'title': act.get('title', ''),
                   'url': act.get('url'), 'first_law': first_law, 'earlier_laws': [], 'versions': versions}
            if prefix:
                rec['path'] = folder
            rec.update(extra.get(act['slug'], {}))
            acts.append(rec)
    Path(a.out).write_text(json.dumps({'laws': laws, 'acts': acts}, ensure_ascii=False, indent=0) + '\n',
                           encoding='utf-8', newline='\n')
    print(f'{len(acts)} acts, {sum(len(x["versions"]) for x in acts)} versions, {len(laws)} laws recovered')


if __name__ == '__main__':
    main()
