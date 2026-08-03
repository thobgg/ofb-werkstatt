# parish-scribe

A tool for **extending** a genealogical dataset from parish registers: read a
page, match it against what you already have, link or create — and export to
GEDCOM when you're done.

> **Work in progress.** Being built against a real dataset (parish registers of
> Haberschlacht, Württemberg, from 1808 onwards). Not yet usable by others.
>
> Built for a **single researcher** transcribing their own parish — no accounts,
> no hosting, no multi-user setup. People who transcribe a parish do so out of a
> personal connection to the place; they are individuals, not a crowd, and each
> has their own village, dataset and handwriting.

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

## An LLM is required, not optional

The whole point is *machine reads first, human corrects*. Without that, this is
just another data entry form — and Ahnenblatt, Gramps and webtrees already have
those. An API key (Anthropic) is therefore a prerequisite, not an add-on.

Cost is roughly 0.13 USD per page, paid by whoever supplies the key. That rules
out a self-contained offline bundle: either every user brings their own key, or
whoever hosts the service supplies one and carries the cost.

Two parts of the code do run without a model — dataset maintenance (duplicate
detection, equivalence classes, integrity checks) and GEDCOM export. Useful, but
not the reason this project exists.

## What is missing

**The core is not built yet.** Everything around it is: database, search,
family linking, equivalence classes, change journal, export, entry form. The
transcription itself is currently done by hand outside the tool.

| | |
|---|---|
| ⬜ | API client, key from configuration |
| ⬜ | page segmentation: overview → row boundaries → one strip per entry |
| ⬜ | transcription prompt, including the known error patterns of the scribe's hand |
| ⬜ | parsing the response into the record structure |
| ⬜ | anchor matching as an automatic step after reading |

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

German is the primary language: code, comments, configuration keys and the user
interface. The registers being transcribed are German, and so are the people
this is built for.

Interface strings are to be separated from the code so other languages can be
added without touching logic. Not done yet.
