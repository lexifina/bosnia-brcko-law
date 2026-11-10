# Brčko District: law history in git

Part of [lexifina/global-law](https://github.com/lexifina/global-law), one git history for every country's law: this is the law of Brčko District, Bosnia and Herzegovina, which global-law reads at `bosnia-and-herzegovina/brcko/acts/`.

The law of Brčko District of Bosnia and Herzegovina (Brčko distrikt Bosne i Hercegovine) as a git history: one file per article, one commit per change, dated the day it took effect. `git log` lists every change to an article; checking out a date gives the text in force that day.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ba-brc/`. The state's own law is in [lexifina/bosnia-and-herzegovina-law](https://github.com/lexifina/bosnia-and-herzegovina-law).

The text is in Bosnian (Latin script), exactly as the Assembly publishes it.

## What this repository holds

Every law in the Assembly's register is accounted for: published here, or listed with the reason in [data/held.json](data/held.json).

- `statut/`: the Statute of Brčko District (Statut Brčko distrikta Bosne i Hercegovine), in the consolidated text the Assembly publishes (Službeni glasnik Brčko distrikta BiH 2/10).
- One folder per law at the top level (the first build, 2026-10-30): laws whose current text the register gives, either the law as adopted, where the register lists no amending act, or the newest official consolidated text (prečišćeni tekst), where nothing was published after it.
- `zakon/<year>/sg<issue>-<id>/` (later builds; indexes in [registry/ACTS.md](registry/ACTS.md) and [registry/data/acts.json](registry/data/acts.json)):
  - amending laws whose own day of effect is counted from their adoption;
  - laws amended after their newest official text, with no official consolidated text since: the newest official text the register holds (the law as adopted, or the last consolidated text), marked `amended, not consolidated`; `amended_by` in registry/data/acts.json names every later file (gazette number, title, link).

Held back, with the reason, in data/held.json: laws whose day of effect is counted from their publication in the gazette (the gazette's publication days are not freely available, so the day cannot be known), texts that do not split into articles or that a second, independent PDF reader does not confirm, and registers that list only amending files. Annual budget-execution laws are out of scope.

## Source

The Assembly of Brčko District (Skupština Brčko distrikta BiH), <https://skupstinabd.ba/>: its register of laws (<https://skupstinabd.ba/index.php/ba/zakon.html>), which gives each law's adopted text, amending acts and consolidated texts as PDFs, with their numbers in the Službeni glasnik Brčko distrikta BiH; and the Statute (<https://skupstinabd.ba/images/dokumenti/ba/statut-brcko-distrikta.pdf>). Every commit names the PDF it was read from (`Source:` or `Consolidated:` trailer), and every act its register page.

## Dates

- A law as adopted is dated the day its own last article names, counted from its adoption (the session day in the enacting formula, which must equal the date under the text).
- A consolidated text, and the first build's laws, are dated by the creation day of the Assembly's published PDF, never before the act was signed: the oldest version available. The gazette's publication dates are not on the Assembly's free site, so this is not the day the text first took effect.
- The commit for each act names the gazette issue that published it. Each commit is dated at noon, Europe/Sarajevo.

## Files

`<act>/clan-001.md` is Član 1, `clan-005-a.md` Član 5a. `uvod.md` holds the enacting formula and the title; `potpis.md` the number, place, date and signature. Chapter headings stay in the file of the first article after them. The Assembly's letterhead, page numbers and a converter's watermark found in one file are left out. One paragraph per line.

In the Statute's PDF the font maps the letters č, Č, ž, Ž and đ to other code points (ĉ, Ĉ, ţ, Ţ, Ď, Ċ); they are restored one for one.

## How it is checked

- Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`); appends read every published act back before adding anything.
- Every paragraph's letters and digits are found in the source PDF as read by a second, independent PDF reader, with a third reader where the second scrambles the reading order.
- Health checks: no merge commits, commit dates never go backwards, nothing dated in the future, and every commit's trailers parse.

## Freshness

<!-- freshness-summary -->
Checked against the official sources: 2026-11-10; 100% of acts verified in the last 7 days, 100% in the last 30 ([data/freshness.json](data/freshness.json)).
<!-- /freshness-summary -->

`python tools/freshness.py <act>` gives an act's status, its last check and the official link. A refresh runner re-reads the Assembly's whole register every day (at most two requests a second), appends new laws and writes these files; [data/status.json](data/status.json) says whether updates are running and whether the source is answering. Acts the register shows as amended with no official consolidated text are marked `amended, not consolidated` and name the amending acts ([registry/data/acts.json](registry/data/acts.json)); laws held back are listed with the reason in [data/held.json](data/held.json), and laws passed but not yet in force in [data/pending.json](data/pending.json). Statuses and fields: [data/freshness.json](data/freshness.json).

## Limits

This is not an official publication. The binding text is the one published in the Službeni glasnik Brčko distrikta BiH. The history starts with the oldest version available, and only the acts listed in `data/versions.json` and `registry/data/acts.json` are included.
