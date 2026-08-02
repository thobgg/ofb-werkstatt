# parish-scribe

A tool for **extending** a genealogical dataset from parish registers: read a
page, match it against what you already have, link or create — and export to
GEDCOM when you're done.

> **Work in progress.** Being built against a real dataset (parish registers of
> Haberschlacht, Württemberg, from 1808 onwards). Not yet usable by others.

## Why

Ahnenblatt, Gramps and webtrees are good at *managing* a dataset but tedious at
*extending one from a source*. Every register entry poses the same question —
**find and use** or **create** — and answering it costs many clicks. Here that
question is pre-answered and only needs confirming.

## Approach

**Record close to the source, not close to GEDCOM.** One row per register entry,
as written. GEDCOM output is derived from it. This way an attribution can be
corrected without touching the reading, and vice versa.

**Change journal instead of mutation.** The original dataset is never modified.
Every addition and correction is a recorded operation with its evidence; the
output file is generated from them. Undo means deactivating an operation.

**Evidence, not verdicts.** Not "confidence level A", but *what* a statement
rests on: `marriage anchor F1149, 14 Feb 1798`. The verdict follows from the
evidence, not the other way round.

**The dataset grows with you.** Without an existing GEDCOM, find-and-use matches
against your own earlier entries: the first hundred build the vocabulary for the
next thousand.

## Status

| | |
|---|---|
| ✅ | GEDCOM index in SQLite, lossless round-trip (byte-identical) |
| ✅ | Equivalence classes for name variants, including detection of bad links |
| ✅ | Duplicate detection via married-couple signature |
| ✅ | Browser entry form with image strip, autocomplete, family linking |
| 🚧 | Generalisation: configuration instead of hard-coded fields |
| 🚧 | Workflow: pick register → pick pages → work |
| ⬜ | GEDCOM export of newly recorded entries |
| ⬜ | Double-click bundle, no Python installation required |

## Configuration

Everything place-specific lives in `konfig.toml` — register types, fields,
defaults, and the optional existing dataset:

```toml
[bestand]
gedcom = ""          # empty = start from scratch

[register.taufe]
titel    = "Baptisms"
ordner   = "bilder/taufe"
personen = ["kind", "vater", "mutter"]
```

## Legal note

Scans from Archion, Ancestry and similar services **must not be redistributed**.
`bilder/` and `daten/` are therefore excluded from version control and do not
belong in a public repository.

## Language

Code, comments and configuration keys are currently in German, as is the user
interface. Translation is planned but not done — contributions welcome once the
core stabilises.
