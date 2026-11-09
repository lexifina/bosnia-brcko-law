"""Freshness files (romania-law format) for the Bosnian sub-national repositories: Brčko District and the cantons
(2026-11-09). Shared by freshness_bd.py, freshness_tk.py, freshness_zdk.py, freshness_sbk.py, freshness_bpk.py.

Method "gazette-index" (cantons) / "register-index" (Brčko): the act counts as checked on the day its source's whole
index was last read through its newest entry (<src>/refresh-state.json) and scanned for amendments, repeals and
consolidated texts of it. An act whose source lists a change this repository does not apply carries the label
"amended, not consolidated" (data/acts.json: status, amended_by) and is pending-change; otherwise current.

Every act on main is a row: the original builds' acts (data/versions.json at the root) and the appended ones
(registry/data/acts.json). Rows give each act's official page.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'world-law' / 'balkan-builder' / 'freshness'))
import freshness_write as FW  # noqa: E402
from commit_files import commit  # noqa: E402

THRESHOLDS = {
    'laws': {'days': 7, 'kinds': ['statut', 'ustav', 'zakon', 'law'],
             'label': 'the Statute or Constitution and the laws'},
}
MONITOR = ('`python tools/freshness.py <act>` gives an act\'s status, its last check and the official link. A refresh '
           'runner re-reads the official source every day (at most two requests a second), appends new laws and '
           'writes these files; [data/status.json](data/status.json) says whether updates are running and whether the '
           'source is answering. Acts the source shows as amended with no official consolidated text are marked '
           '`amended, not consolidated` and name the amending acts ([data/acts.json](registry/data/acts.json)); acts '
           'held back are listed with the reason in [data/held.json](data/held.json), and acts passed but not yet in '
           'force in [data/pending.json](data/pending.json).')


def git(repo: Path, *a: str) -> str:
    return subprocess.run(['git', *a], cwd=repo, capture_output=True, text=True, encoding='utf-8').stdout


def main_acts(repo: Path) -> list[dict]:
    acts = {}
    p = repo / 'data' / 'versions.json'
    if p.exists():
        for a in json.loads(p.read_text(encoding='utf-8'))['acts']:
            if (repo / a['slug']).exists():
                kind = 'statut' if a['slug'].startswith('statut') else 'ustav' if a['slug'].startswith('ustav') else 'zakon'
                acts[a['slug']] = {'slug': a['slug'], 'path': f'{kind}/root/{a["slug"]}', 'folder': a['slug'],
                                   'kind': kind, 'title': a.get('title'), 'portal': a.get('url'),
                                   'source_url': a['versions'][-1].get('source_url') if a.get('versions') else None,
                                   'status': 'in force'}
    p = repo / 'registry' / 'data' / 'acts.json'
    if p.exists():
        for a in json.loads(p.read_text(encoding='utf-8'))['acts']:
            if a.get('path') and (repo / a['path']).exists():
                prev = acts.get(a['slug'], {})
                acts[a['slug']] = {**prev, 'slug': a['slug'], 'path': a['path'] if a['path'] != a['slug'] else prev.get('path', a['path']),
                                   'folder': a['path'], 'kind': prev.get('kind') or a.get('kind') or 'zakon',
                                   'title': a.get('title'), 'portal': prev.get('portal') or a.get('portal'),
                                   'status': a.get('status'), 'amended_by': a.get('amended_by'), 'latest': a.get('latest')}
    return list(acts.values())


def rows(repo: Path, checked: str | None, as_of: str, method: str) -> list[dict]:
    out = []
    for a in main_acts(repo):
        thr = next((t['days'] for t in THRESHOLDS.values() if a['kind'] in t['kinds']), 30)
        row = {'act': a['slug'], 'path': a['path'], 'kind': a['kind'], 'method': method,
               'official_url': a.get('portal') or a.get('source_url') or '', 'last_verified': checked or '',
               'check_due': '', 'newest_change': '', 'newest_change_date': '', 'change_in_repo': ''}
        repealed = (a.get('status') or '').startswith('repealed')
        if not checked:
            row['status'] = 'unverified'
        elif repealed:
            row['status'] = 'current'
        else:
            row['check_due'] = (dt.date.fromisoformat(checked) + dt.timedelta(days=thr)).isoformat()
            if a.get('amended_by'):
                last = a['amended_by'][-1]
                row.update(status='pending-change', newest_change=f"{last.get('title') or ''} ({last.get('ref') or ''})",
                           newest_change_date=last.get('date') or '', change_in_repo='no')
            else:
                row['status'] = 'current'
            if row['status'] == 'current' and row['check_due'] < as_of:
                row['status'] = 'stale'
        out.append(row)
    return out


def readme_block(text: str, line: str) -> str:
    """Fill the freshness block, adding it (with the monitoring paragraph) under a '## Freshness' heading if absent."""
    if FW.BEGIN in text:
        return FW.fill_readme(text, line)
    block = f'\n## Freshness\n\n{FW.BEGIN}\n{line}\n{FW.END}\n\n{MONITOR}\n'
    i = text.find('\n## Limits')
    return text + block if i < 0 else text[:i] + block + text[i:]


def run(repo: Path, src: Path, code: str, email: str, method: str, method_text: str, source_name: str,
        source_url: str, held: list[dict], pending: list[dict], readme: str | None = None, do_commit: bool = False,
        source_ok: bool = True) -> dict:
    as_of = dt.datetime.now(dt.timezone.utc).date().isoformat()
    st = json.loads((src / 'refresh-state.json').read_text(encoding='utf-8')) if (src / 'refresh-state.json').exists() else {}
    checked = st.get('register_read') or st.get('listing_read') if source_ok else None
    if st.get('scanned_through_listing') is not None and not st.get('scanned_through_listing'):
        checked = None  # the listing was read but its new issues were not all scanned: no act counts as checked
    rs = rows(repo, checked, as_of, method)
    sources = [{'source': source_name, 'url': source_url, 'last_successful_check': checked}]
    status = {'note': 'Update status of this repository, refreshed by every refresh run.',
              'as_of': dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(), 'updates': 'idle',
              'last_published': git(repo, 'log', '-1', '--format=%cI').strip(),
              'published_last_24h': {'commits': len([x for x in git(repo, 'log', '--since=24 hours ago', '--format=%H').splitlines() if x])},
              'official_sources': [{'source': source_name, 'url': source_url,
                                    'state': 'available' if checked else 'unknown',
                                    'last_successful_contact': checked}]}
    meta = {'code': code, 'as_of': as_of, 'checked_against_official_source': checked,
            'methods': {method: method_text}, 'thresholds': THRESHOLDS, 'sources': sources, 'status': status}
    files = FW.write(repo, rs, meta)
    summary = json.loads(files['data/freshness.json'])
    line = FW.summary_line(summary)
    base = readme if readme is not None else (repo / 'README.md').read_text(encoding='utf-8')
    files['README.md'] = readme_block(base, line)
    files['data/held.json'] = json.dumps({'note': 'In-scope acts held back from main, with the reason and the official '
                                                  'page.', 'count': len(held), 'acts': held},
                                         ensure_ascii=False, indent=0) + '\n'
    files['data/pending.json'] = json.dumps({'note': 'Acts published but not yet in force; each is appended on the day '
                                                     'it takes effect.', 'count': len(pending), 'acts': pending},
                                            ensure_ascii=False, indent=0) + '\n'
    files['tools/freshness.py'] = (HERE.parent.parent / 'world-law' / 'balkan-builder' / 'freshness' / 'freshness.py'
                                   ).read_text(encoding='utf-8')
    t = summary['totals']
    res = {'acts': t['acts'], 'by_status': t['by_status'], 'line': line}
    if do_commit:
        res['committed'] = commit(repo, files, f'Freshness: checked against the official source on {checked}\n\n{line}\n', email)
    return res
