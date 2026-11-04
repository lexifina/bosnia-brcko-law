"""Independent check of corpus.d parts against the source PDFs, read by pdftotext (poppler), not the parser's
pymupdf: (1) every paragraph's letters and digits occur in the source; (2) the source's letters and digits not
accounted for (residue) are reported; (3) how many paragraphs are also found in reading order. Private."""
import hashlib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'world-law'))
import ba_lib  # noqa: E402
sys.argv_saved = sys.argv
import parse  # noqa: E402


def main(part, show=3):
    c = json.loads((HERE / 'corpus.d' / part).read_text(encoding='utf-8'))
    bad = 0
    for a in c['acts']:
        for v in a['versions']:
            path = HERE / '.cache' / 'by-url' / hashlib.sha256(v['source_url'].encode()).hexdigest()
            assert ba_lib.sha256(path) == v['sha256'], a['slug']
            src = subprocess.run(['pdftotext', '-enc', 'UTF-8', str(path), '-'], capture_output=True).stdout.decode('utf-8', 'replace')
            ba_lib.WHERE['page'] = 0
            if part.startswith('10-statut'):
                src = src.translate(parse.GLYPHS)
            parse.CYRILLIC_IS_BOILERPLATE = False
            src = re.sub('[Ѐ-ӿ]+', ' ', src)  # the Cyrillic letterhead and duplicate signature, wherever they sit
            # boilerplate that is not law text: page numbers, the running letterhead, a converter's watermark
            src = '\n'.join(l for l in src.splitlines() if not re.fullmatch(r'\s*\d{1,3}\s*', l) and not parse.is_letterhead(l.strip()))
            paras = [l for k, u in v['units'].items() for l in u['text'].splitlines()]
            missing, ours, theirs = ba_lib.check_present(paras, src)
            if missing:  # a paragraph pdftotext reads out of layout order: a third reader, pypdf, must find it
                from pypdf import PdfReader
                alt = ''.join(pg.extract_text() or '' for pg in PdfReader(str(path)).pages)
                missing = ba_lib.check_present(missing, alt)[0]
            inorder, _, _ = ba_lib.check_in_order(paras, src)
            ok = not missing and theirs - ours <= max(400, theirs // 50)
            bad += not ok
            print(('OK  ' if ok else 'FAIL'), a['slug'][:45], f'present {len(paras) - len(missing)}/{len(paras)}, in order {inorder}, letters ours {ours} source {theirs}')
            for m in missing[:show]:
                print('      ', m[:150])
    print('acts failing:', bad)


if __name__ == '__main__':
    main(sys.argv[1])
