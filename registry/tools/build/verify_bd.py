"""Independent check of live/corpus.d/30-registar.json against the source PDFs (the original build's verify.py:
pdftotext and pypdf, not the parser's pymupdf), reading the fetched PDFs in <src>. Private.

    python -X utf8 verify_bd.py --src DIR
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / 'world-law'))
ap = argparse.ArgumentParser()
ap.add_argument('--src', required=True)
ap.add_argument('--part', default='30-registar.json')
a = ap.parse_args()
sys.argv = [sys.argv[0]]
import verify as V  # noqa: E402
V.HERE = Path(a.src) / 'w'  # w/.cache -> <src> (by-url/), w/corpus.d -> live/corpus.d (junctions)
V.main(a.part, show=2)
