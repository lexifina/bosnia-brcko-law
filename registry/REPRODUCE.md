# How this repository was made (Brčko District)

This file is written by the build on 2026-11-04, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Skupština Brčko distrikta BiH: register of laws (PDF texts) | <https://skupstinabd.ba/index.php/ba/zakon.html> | 2026-11-03 | Official text, not protected: Zakon o autorskom i srodnim pravima BiH (Sl. glasnik BiH 63/10), čl. 8(1)(b) |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| 8 acts | every act, with its kind, number, status and span, is listed in [ACTS.md](ACTS.md) | 8 | |

The build made 0 commits:

| Commits | Kind |
| ---: | --- |
| 0 | first version of an act |
| 0 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `buducnost`: laws not yet in force on 2026-11-04.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 8 laws in the record.
- 74 tags.

## Dates

Each commit is dated at noon (Europe/Sarajevo) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: A law takes effect on the day it names, most often the eighth day after its publication in the Službeni glasnik Brčko distrikta BiH. https://skupstinabd.ba/index.php/ba/zakon.html

## How the history is built

`tools/build/build.py` (and, for later publishes, `tools/build/append.py`) turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/build/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/build/SCHEMA.md`.

- Corpus: sha256 `e698d5921caa1769c5d436e6c5bd09270fcff62ecf6c361fc1be5bac980ca27d` (29042 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `6a75a05e2f381deb50fb7cb6ad297cc3fe964a71`, `check.py` `d36188b60926167ff377bd58f0b03f30cc9a1a52`, `on.py` `55bf92027127e36254521d114abde53cfefbb67d`.
- Python 3.14.0; git version 2.52.0.windows.1.

## Checks

Not yet run for this build.

No second build of this corpus has been compared yet.

## Decisions made by hand

- Every act's decisions made by hand (4 in all) are listed in that act's own README.md, under "Decisions made by hand".

## What AI did and did not do

The scripts that read the sources and build this repository were written by Claude Code running Claude Opus 5.5 (`claude-opus-5-5`) under Lexifina's direction.

No model wrote, translated or corrected legal text. No model runs at build time. Every word of law in this repository comes from the official sources above.

The commit messages are written by `build.py` from the source data.

Model use at data-build time:
- none: the text is read from the PDF text layer by a deterministic parser; no model output is legal text.
