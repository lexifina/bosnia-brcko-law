"""History integrity of a published clone, without a corpus: merges, committer times going backwards or in the future,
law commits (with a Law: or Source: trailer) lacking In-force, author day != In-force day, Source trailers present,
tags pointing at commits not on main, committer identities.

    python -X utf8 hist_audit.py <clone>
"""
import collections
import json
import subprocess
import sys
import time

repo = sys.argv[1]
SEP = '\x1e'
out = subprocess.run(['git', 'log', '--first-parent', 'main', f'--format=%H%x1f%P%x1f%ct%x1f%ad%x1f%cn <%ce>%x1f%(trailers:key=In-force,valueonly,separator=,)%x1f%(trailers:key=Source,valueonly,separator=,)%(trailers:key=Consolidated,valueonly,separator=,)%x1f%(trailers:key=Law,valueonly,separator=,)%x1f%(trailers:key=Kind,valueonly,separator=,){SEP}',
                      '--date=format:%Y-%m-%d'], cwd=repo, capture_output=True, text=True, encoding='utf-8').stdout
rows = [r.strip('\n').split('\x1f') for r in out.split(SEP) if r.strip()]
rows.reverse()
res = collections.Counter()
committers = collections.Counter()
prev = 0
now = time.time()
bad = []
for h, p, ct, ad, who, inf, src, law, kind in rows:
    ct = int(ct)
    committers[who] += 1
    res['commits'] += 1
    if len(p.split()) > 1:
        res['merges'] += 1
    if ct < prev:
        res['backwards'] += 1
    if ct > now + 60:
        res['future_dated'] += 1
    prev = max(prev, ct)
    if law or src or inf:
        res['law_commits'] += 1
        if not inf:
            res['missing_in_force'] += 1
            bad.append(('no In-force', h[:10]))
        elif inf[:10] != ad and ad != '1970-01-01':
            res['author_day_ne_in_force'] += 1
            bad.append(('author day', h[:10], ad, inf))
        if not src:
            res['no_source'] += 1
main = set(r[0] for r in rows)
tags = subprocess.run(['git', 'for-each-ref', '--format=%(objectname) %(*objectname) %(refname:short)', 'refs/tags'], cwd=repo,
                      capture_output=True, text=True).stdout.split('\n')
for t in tags:
    if not t.strip():
        continue
    o, peeled, name = t.split(' ', 2) if t.count(' ') >= 2 else (t.split(' ')[0], '', t.split(' ')[-1])
    target = peeled or o
    res['tags'] += 1
    if target not in main:
        res['tags_off_main'] += 1
        bad.append(('tag off main', name))
print(json.dumps({'counts': res, 'committers': committers, 'examples': bad[:15]}, ensure_ascii=False, indent=1))
