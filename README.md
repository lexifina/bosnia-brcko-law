# Brčko District: law history in git

The law of Brčko District of Bosnia and Herzegovina (Brčko distrikt Bosne i Hercegovine) as a git history: one file per article, one commit per change, dated the day it took effect. `git log` lists every change to an article; checking out a date gives the text in force that day.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `ba-brc/`. The state's own law is in [lexifina/bosnia-and-herzegovina-law](https://github.com/lexifina/bosnia-and-herzegovina-law).

The text is in Bosnian (Latin script), exactly as the Assembly publishes it.

## What this repository holds

- `statut/`: the Statute of Brčko District (Statut Brčko distrikta Bosne i Hercegovine), in the consolidated text the Assembly publishes (Službeni glasnik Brčko distrikta BiH 2/10), which laws of 2022 to 2026 still cite as the Statute.
- One folder per law: the laws in the Assembly's register whose current text the register gives, either
  - the law as adopted, where the register lists no amending act, or
  - the newest official consolidated text (prečišćeni tekst), where nothing was published after it.

Laws amended after their latest official consolidation are not included yet, nor laws whose PDF has no text layer. Annual budget-execution laws are left out.

## Source

The Assembly of Brčko District (Skupština Brčko distrikta BiH), <https://skupstinabd.ba/>: its register of laws (<https://skupstinabd.ba/index.php/ba/zakon.html>), which gives each law's adopted text, amending acts and consolidated texts as PDFs, with their numbers in the Službeni glasnik Brčko distrikta BiH; and the Statute (<https://skupstinabd.ba/images/dokumenti/ba/statut-brcko-distrikta.pdf>).

## Dates

- Each act has one version: the oldest version available. It is dated by the creation date of the Assembly's published PDF, and never before the date the act was signed. The gazette's publication dates are not on the Assembly's free site, so this is not the day the text first took effect.
- The commit for each act names the gazette issue that published it.
- Each commit is dated at noon, Europe/Sarajevo.

## Files

`<act>/clan-001.md` is Član 1, `clan-005-a.md` Član 5a. `uvod.md` holds the enacting formula and the title; `potpis.md` the number, place, date and signature. Chapter headings stay in the file of the first article after them. The Assembly's letterhead, page numbers and a converter's watermark found in one file are left out. One paragraph per line.

In the Statute's PDF the font maps the letters č, Č, ž, Ž and đ to other code points (ĉ, Ĉ, ţ, Ţ, Ď, Ċ); they are restored one for one.

## How it is checked

- Every version is read back from git on the day it took effect and on the day before (`tools/check_repo.py`); both must match `corpus.json`.
- Every paragraph's letters and digits are found in the source PDF as read by a second, independent PDF reader, with a third reader where the second scrambles the reading order; the letters and digits the source holds beyond ours are only the letterhead, page numbers and watermark.
- Health checks: no merge commits, commit dates never go backwards, nothing dated in the future, and every commit's trailers parse.

## Limits

This is not an official publication. The binding text is the one published in the Službeni glasnik Brčko distrikta BiH. The history starts with the oldest version available, and only the acts listed in `data/versions.json` are included.
