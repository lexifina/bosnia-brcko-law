"""Brčko District: every law in the Assembly's register (<src>/register.json) against main; writes the census, the
holds, and a corpus part with the laws main lacks (2026-11-09, romania-law standard). Private (never published).

    python -X utf8 parse_bd.py --src DIR --repo CLONE --out corpus.d [--retrieved YYYY-MM-DD]

Reads <src>/register.json and <src>/by-url/ (fetch_bd.py) and the clone's data/versions.json and
registry/data/versions.json. Writes:
- <out>/30-registar.json: one act per register law main does not hold, when its text can be read and dated:
  - amended, with no official consolidated text after the last amendment: the newest base text the register holds
    (the law as adopted, or the last official consolidated text), labelled "amended, not consolidated", with
    amended_by = every later file the register lists (gazette number, title, link);
- <src>/census.json (per law: on main / added / held, with the reason), <src>/held.json, <src>/labels.json
  (labels for the published acts the register shows as amended after their text: recover_acts.py --extra).

Dating (as for the acts another build already appended under zakon/): a law as adopted takes effect on the day its own
last article names when that day is counted from adoption ("danom donošenja/usvajanja" = the session day in the
enacting formula, which must equal the date under the text; "N-og dana od dana donošenja"; or a calendar date). A day
counted from publication cannot be known: the gazette's publication days are not freely available, so such a law is
held. A consolidated text is dated as the original build dated them: the creation day of the Assembly's PDF, never
before the day it was signed, as the oldest version available (credited to the publisher).
Deterministic: the same inputs give the same bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / 'world-law'))
import ba_lib  # noqa: E402
import parse as P  # noqa: E402  (the original build's reader: units_of, signed_date, pdf_date, title_of)

AMEND = re.compile(r'(?i)izmjen|dopun|presuda|odluka|pismo|ispravk|tumac|tumač|supervizor|amandman|prestanku')
CONS = P_CONS = re.compile(r'(?i)pre[c+]?(-|\+)*i?s(-|\+)*c?(-|\+)*c?(-|\+)*e?n|precisc|prec--is')
BUDGET = re.compile(r'(?i)izvr(s--|š|s)enju bud(z--|ž|z)eta|^/?bud(z--|ž)et')
NUM = {'prvog': 1, 'drugog': 2, 'trećeg': 3, 'treceg': 3, 'četvrtog': 4, 'petog': 5, 'šestog': 6, 'sedmog': 7,
       'osmog': 8, 'devetog': 9, 'desetog': 10, 'petnaestog': 15, 'tridesetog': 30}
MONTHS = {'januar': 1, 'februar': 2, 'mart': 3, 'april': 4, 'maj': 5, 'jun': 6, 'juni': 6, 'jul': 7, 'juli': 7,
          'august': 8, 'avgust': 8, 'septembar': 9, 'oktobar': 10, 'novembar': 11, 'decembar': 12}
FIXED_ADOPT = re.compile(r'(?i)stupa(ju)?\s+na\s+snagu\s+(sa\s+danom|danom|dan)\s+(njegovog\s+|njihovog\s+)?(dono[sš]enja|usvajanja)')
DAYS_ADOPT = re.compile(r'(?i)stupa(ju)?\s+na\s+snagu\s+(\w+)\s*(\((\d+)\)\s*)?dana\s+(od\s+dana|nakon|poslije|po)\s+(njegovog\s+|njihovog\s+|ovog\s+zakona\s+)?(dono[sš]enja|usvajanja)')
PUBL = re.compile(r'(?i)stupa(ju)?\s+na\s+snagu.{0,60}?dana\s+(od\s+dana\s+|nakon\s+|po\s+|poslije\s+)?(njegovog\s+|njihovog\s+)?objav|stupa(ju)?\s+na\s+snagu\s+(danom|dan|na\s+dan)\s+(njegovog\s+)?objav')
SESSION = re.compile(r'(?i)održanoj\s+(\d{1,2})\s*\.\s*([a-zčćšž]+)\s+(\d{4})')
SESSION_NUM = re.compile(r'(?i)održanoj\s+(\d{1,2})\s*\.\s*(\d{1,2})\s*\.\s*(\d{4})')


def month(w: str):
    w = w.lower()
    for k, v in MONTHS.items():
        if w.startswith(k[:3]) and (w.startswith(k) or w[:-1] == k or w[:-2] == k):
            return v
    return None


def session_day(text: str):
    m = SESSION.search(text)
    if m and month(m.group(2)):
        return date(int(m.group(3)), month(m.group(2)), int(m.group(1)))
    m = SESSION_NUM.search(text)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def in_force(units: dict):
    """(day, rule) or (None, why) from the law's own text: its last article, counted from the session day."""
    arts = [k for k in units if k.startswith('clan-')]
    last = units[arts[-1]]['text'] if arts else ''
    uvod = units.get('uvod', {}).get('text', '')
    sess = session_day(uvod) or session_day(units.get('potpis', {}).get('text', ''))
    signed = P.signed_date(units.get('potpis', {}).get('text', '').split('\n'))
    if sess and signed and sess.isoformat() != signed:
        return None, f'session day {sess} in the enacting formula differs from the date under the text {signed}'
    if PUBL.search(last) and not FIXED_ADOPT.search(last) and not DAYS_ADOPT.search(last):
        return None, 'in force from a day counted from its publication; the gazette\'s publication days are not freely available'
    if FIXED_ADOPT.search(last):
        if not sess:
            return None, 'in force on the day of adoption, but the session day is not readable'
        return sess, 'the day of adoption (its last article)'
    m = DAYS_ADOPT.search(last)
    if m:
        n = int(m.group(4)) if m.group(4) else NUM.get(m.group(2).lower())
        if not n or not sess:
            return None, 'in force a number of days after adoption, but the number or the session day is not readable'
        return sess + timedelta(days=n), f'the {n}th day after adoption (its last article)'
    m = re.search(r'(?i)stupa(ju)?\s+na\s+snagu\s+(\d{1,2})\s*\.\s*([a-zčćšž]+)\s+(\d{4})', last)
    if m and month(m.group(3)):
        return date(int(m.group(4)), month(m.group(3)), int(m.group(2))), 'a calendar day (its last article)'
    return None, 'its last article names no in-force day this parser can read'


def gazette(issue):
    return f'Službeni glasnik Brčko distrikta BiH {issue[1]}/{issue[0] % 100:02d}' if issue else 'gazette number not given'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--retrieved', default=None)
    a = ap.parse_args()
    src, repo, out = Path(a.src), Path(a.repo), Path(a.out)
    retrieved = a.retrieved or json.loads((src / 'refresh-state.json').read_text())['register_read']
    reg = json.loads((src / 'register.json').read_text(encoding='utf-8'))
    on_main = {}
    for rel in ('data/versions.json', 'registry/data/versions.json'):
        p = repo / rel
        if p.exists():
            for act in json.loads(p.read_text(encoding='utf-8'))['acts']:
                if (repo / (act.get('path') or act['slug'])).exists():
                    on_main[act['slug']] = act
    by_page = {v.get('url'): s for s, v in on_main.items() if v.get('url')}
    by_file = {}
    for s, v in on_main.items():
        for ver in v['versions']:
            by_file[ver.get('source_url')] = s
    census, held, labels = {}, {}, {}
    part = {'sources': [], 'laws': {}, 'acts': [], 'applies': [], 'decisions': [], 'ai_use': []}

    def path_of(u):
        return src / 'by-url' / hashlib.sha256(u.encode()).hexdigest()

    # acts whose text the independent check (verify_bd.py) did not confirm: {act slug: reason}
    vf = src / 'verify-failed.json'
    failed = json.loads(vf.read_text(encoding='utf-8')) if vf.exists() else {}
    for law_id in sorted(reg):
        e = reg[law_id]
        title = P.title_of(law_id)
        files = sorted(e['files'], key=lambda f: (f['issue'] or [0, 0], f['name']))
        row = {'law': law_id, 'title': title, 'page': e['page'], 'files': len(files)}
        slug = by_page.get(e['page'])
        if slug:
            ver = on_main[slug]['versions'][-1]
            idx = next((i for i, f in enumerate(files) if f['url'] == ver.get('source_url')), None)
            later = files[idx + 1:] if idx is not None else []
            row.update(state='on main', act=slug)
            if idx is None:
                row['note'] = 'its published file is no longer in the register'
            elif later:
                labels[slug] = {'label': 'amended, not consolidated',
                                'amended_by': [{'ref': gazette(f['issue']), 'title': f['name'][:-4], 'url': f['url']} for f in later]}
                row['note'] = f'amended after its published text by {len(later)} files'
            census[law_id] = row
            continue
        if not files:
            row.update(state='held', why='the register page lists no file')
            census[law_id] = held[law_id] = row
            continue
        if BUDGET.search(law_id):
            row.update(state='held', why='annual budget-execution law (temporary), out of scope')
            census[law_id] = held[law_id] = row
            continue
        # files without a gazette number: unofficial consolidations (not official texts) are set aside; any other
        # (a court judgment, a correction) is a change after every numbered file
        unofficial = [f for f in files if not f['issue'] and re.search(r'(?i)nesl', f['name'])]
        files = [f for f in files if f['issue']] + [f for f in files if not f['issue'] and f not in unofficial]
        if unofficial:
            row['unofficial_consolidations'] = [f['name'] for f in unofficial]
        cons = [i for i, f in enumerate(files) if CONS.search(f['name']) and f['issue']]
        base_i = cons[-1] if cons else next((i for i, f in enumerate(files) if f['issue'] and not AMEND.search(f['name'])), None)
        if base_i is None:
            row.update(state='held', why='the register lists only amending files (no original or consolidated text)')
            census[law_id] = held[law_id] = row
            continue
        base, later = files[base_i], files[base_i + 1:]
        if any(by_file.get(f['url']) for f in files):
            row['note'] = 'an amending file of this law is published as its own act: ' + ', '.join(by_file[f['url']] for f in files if by_file.get(f['url']))
        p = path_of(base['url'])
        if not p.exists():
            row.update(state='held', why='PDF not fetched (the publisher did not serve it)')
            census[law_id] = held[law_id] = row
            continue
        try:
            units, paras = P.units_of(p)
        except Exception as ex:  # noqa: BLE001
            units, paras = None, f'unreadable PDF ({type(ex).__name__})'
        if units is None:
            row.update(state='held', why=f'text does not split into articles: {paras}')
            census[law_id] = held[law_id] = row
            continue
        is_cons = bool(cons)
        signed = P.signed_date(units.get('potpis', {}).get('text', '').split('\n') + paras[-12:])
        if is_cons:
            created = P.pdf_date(p)
            if not created or (signed and created < signed):
                row.update(state='held', why=f'consolidated text with no usable file date (created {created}, signed {signed})')
                census[law_id] = held[law_id] = row
                continue
            day, rule = created, 'the creation day of the Assembly\'s PDF (oldest version available)'
        else:
            d, rule = in_force(units)
            if d is None:
                row.update(state='held', why=rule)
                census[law_id] = held[law_id] = row
                continue
            day = d.isoformat()
        if day > retrieved:
            row.update(state='pending', why=f'in force from {day}, after the register was read')
            census[law_id] = held[law_id] = row
            continue
        y, num = base['issue']
        aslug = f'zakon-{y}-sg{num:03d}-' + hashlib.sha1(base['url'].encode()).hexdigest()[:6]
        lk = aslug
        part['laws'][lk] = {'label': f'{title} ("Službeni glasnik Brčko distrikta BiH", broj {num}/{y % 100:02d})'
                                     + (' (prečišćeni tekst)' if is_cons else ''),
                            'title': title, 'kind': 'law', 'enacted': None if is_cons else signed,
                            'published': None, 'url': base['url'], 'temporary_until': None, 'restores': None,
                            'note': None}
        act = {'slug': aslug, 'short': title[:60].rstrip(' ,-'), 'title': title, 'url': e['page'],
               'first_law': None if is_cons else lk, 'earlier_laws': [lk] if is_cons else [],
               'versions': [{'from': day, 'source_url': base['url'], 'sha256': ba_lib.sha256(p), 'units': units,
                             'note': (f'Official consolidated text (prečišćeni tekst), {gazette(base["issue"])}; dated by '
                                      f'{rule}.' if is_cons else
                                      f'The law as adopted ({gazette(base["issue"])}), in force on {rule}.')}]}
        if later:
            act['label'] = 'amended, not consolidated'
            act['amended_by'] = [{'ref': gazette(f['issue']), 'title': f['name'][:-4], 'url': f['url']} for f in later]
            act['versions'][0]['note'] += (f' The register lists {len(later)} later amending file(s) with no official '
                                           'consolidated text: this is the text before them (amended, not consolidated).')
        if aslug in failed:
            row.update(state='held', why='independent text check failed: ' + failed[aslug])
            census[law_id] = held[law_id] = row
            continue
        part['acts'].append(act)
        row.update(state='added', act=aslug, base=base['name'], day=day, amended_after=len(later))
        census[law_id] = row
    part['sources'].append({'name': 'Skupština Brčko distrikta BiH: register of laws (PDF texts)',
                            'url': 'https://skupstinabd.ba/index.php/ba/zakon.html', 'retrieved': retrieved,
                            'licence': P.LICENCE})
    part['decisions'] += [
        'Register laws the earlier builds did not publish because they were amended with no official consolidated text '
        'after the amendments are published as their newest base text (the law as adopted, or the last official '
        'consolidated text) and labelled "amended, not consolidated"; the later amending files are listed in '
        'data/acts.json (amended_by).',
        'A law as adopted is dated by its own last article when that day is counted from adoption (the session day in '
        'the enacting formula must equal the date under the text); a day counted from publication cannot be known '
        '(the gazette\'s publication days are not freely available), so such a law is held (data/held.json).',
        'A consolidated text is dated by the creation day of the Assembly\'s PDF, never before it was signed, as the '
        'oldest version available.',
        'Annual budget-execution laws are out of scope (temporary).']
    part['ai_use'].append('none: the text is read from the PDF text layer by a deterministic parser; no model output is legal text.')
    out.mkdir(exist_ok=True)
    tmp = out / '30-registar.json.tmp'
    tmp.write_text(json.dumps(part, ensure_ascii=False, indent=0) + '\n', encoding='utf-8', newline='\n')
    tmp.replace(out / '30-registar.json')
    for name, obj in (('census.json', census), ('held.json', held), ('labels.json', labels)):
        (src / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    from collections import Counter
    print(json.dumps({'register_laws': len(reg), 'states': Counter(r['state'] for r in census.values()),
                      'added_amended': sum(1 for x in part['acts'] if x.get('label')),
                      'labels_on_main': len(labels),
                      'held_reasons': Counter(r['why'].split(':')[0][:70] for r in held.values())}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
