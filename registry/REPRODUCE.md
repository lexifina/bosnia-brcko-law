# How this repository was made (Brčko District)

This file is written by the build on 2026-11-09, the day the source data was retrieved.

## Sources

| Source | Address | Retrieved | Licence |
| --- | --- | --- | --- |
| Skupština Brčko distrikta BiH: register of laws (PDF texts) | <https://skupstinabd.ba/index.php/ba/zakon.html> | 2026-11-03 | Official text, not protected: Zakon o autorskom i srodnim pravima BiH (Sl. glasnik BiH 63/10), čl. 8(1)(b) |
| Skupština Brčko distrikta BiH: register of laws (PDF texts) | <https://skupstinabd.ba/index.php/ba/zakon.html> | 2026-11-09 | Official text, not protected: Zakon o autorskom i srodnim pravima BiH (Sl. glasnik BiH 63/10), čl. 8(1)(b) |

Every word of law in this repository comes from these sources. Lexifina reads them and records each act's dated versions, and the laws that made each change, in one corpus file. This repository is built from that file.

## What is in it

| Act | Title | Versions | Span |
| --- | --- | ---: | --- |
| 94 acts | every act, with its kind, number, status and span, is listed in [ACTS.md](ACTS.md) | 94 | |

The build made 28 commits:

| Commits | Kind |
| ---: | --- |
| 28 | first version of an act |
| 0 | one law on its in-force day |
| 0 | changes no amendment note explains, credited to the publisher |

Other counts:
- 0 commits on the branch `buducnost`: laws not yet in force on 2026-11-09.
- 0 commits dated 1 January 1970: in force before 1970, with the real day in their `In-force` trailer.
- 100 laws in the record.
- 103 tags.

## Dates

Each commit is dated at noon (Europe/Sarajevo) on the day the change took effect. The other dates, enacted and published, are trailers.

When a law gives no date of its own, the default rule applies: A law takes effect on the day it names, most often the eighth day after its publication in the Službeni glasnik Brčko distrikta BiH. https://skupstinabd.ba/index.php/ba/zakon.html

## How the history is built

`tools/build/build.py` (and, for later publishes, `tools/build/append.py`) turns the corpus into this history in one pass: one commit per law, on the day it took effect. The same corpus always gives the same commit hashes. `tools/build/check_repo.py` reads every version back from git and compares it with the corpus. `tools/on.py` shows the law as it stood on any date. The corpus format is described in `tools/build/SCHEMA.md`.

- Corpus: sha256 `970441297419b89f26df792b9a721a35bb31104ae23173ff0dcc121236fba1e6` (6123504 bytes).
- Builder blob hashes (`git hash-object`): `build.py` `ca294ab3d2553b6e8322e838325b576a0939da6b`, `check.py` `f7f9c39fff1b1f9a3aded2ad3364a27fb0908033`, `on.py` `0be88de7820b2dafe9f94fa40472a48776aa4cf5`.
- Python 3.12.10; git version 2.46.0.windows.1.

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
