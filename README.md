# SlashFilm Gilligan Investigation

Catalog and analyze SlashFilm coverage across a calendar year, with special attention to coverage of *Gilligan's Island* and its principal cast. The central question is whether SlashFilm covers this 60-year-old sitcom and its cast unusually often compared with culturally prominent properties such as Batman or *Breaking Bad*.

## Project goals

- Build a reproducible catalog of SlashFilm stories.
- Classify each story by primary subject.
- Measure Gilligan-related coverage against major comparison IP.
- Generate charts showing coverage volume and share.

## Repository layout

- `data/catalog.csv` — article-level catalog
- `data/README.md` — data handling notes
- `scripts/` — collection, cleaning, and chart-generation code
- `charts/` — generated visualizations and chart notes
- `reports/` — written findings and research outputs

## Data fields

The core catalog uses:

`title,date,subject,gilligan_related`

Supporting fields include `url`, `author`, `section`, `published_at`, `subject_type`, and `notes` for verification and analysis.

## Classification rules

`gilligan_related` is `yes` when the story is primarily about *Gilligan's Island*, its franchise, or one of its principal cast members: Alan Hale Jr., Bob Denver, Natalie Schafer, Jim Backus, Tina Louise, Russell Johnson, or Dawn Wells. A passing mention does not qualify.

The `subject` field should identify the main subject rather than every person or property mentioned. Examples: `Alan Hale Jr.`, `Spider-Man`, `Various Western Films`, or `Project Hail Mary`.

Dates should preserve SlashFilm's displayed publication timestamp. Analysis scripts should normalize timestamps to a documented timezone and retain the original value for auditability.

## Reproducibility

Each catalog row should include the source URL. Headline-derived classifications are acceptable when unambiguous; confusing headlines should be checked with a brief article read and explained in `notes`. Do not silently infer missing publication dates.

## Scope

Initial scope: SlashFilm stories published during 2026, beginning January 1 and continuing through the current date.

## Status

Repository setup is complete. Data collection and charting are next.
