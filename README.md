# SlashFilm Gilligan Investigation

A data-backed answer to a very specific question: why does SlashFilm seem to publish so many stories about *Gilligan's Island* and its cast?

The completed catalog contains 68,398 SlashFilm stories published from 2020 through Aug. 2, 2026. The accompanying report finds 204 Gilligan-related stories from 2024 through that date, including 110 in 2024 alone. The Gilligan Universe appears more often in this data window than *The Simpsons*, *Stranger Things*, *Harry Potter*, *The Pitt*, and *Breaking Bad*.

## Project goals

- Preserve a reproducible catalog of SlashFilm stories.
- Classify each story by primary subject.
- Measure Gilligan-related coverage against selected franchises and current TV shows.
- Generate the finished, public-facing investigation packet.

## Repository layout

- `data/catalog_processed_<year>.csv` — canonical processed article catalogs for 2020-2026
- `scripts/build_gilligan_report.py` — reproducibly builds the report and its charts
- `output/pdf/slashfilm-gilligans-island-coverage-report.pdf` — finished report packet
- `reports/gilligan_report_metrics.json` — derived report metrics
- `data/`, `scripts/`, `charts/`, and `reports/` — supporting notes and project assets

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

## Status

The initial investigation is complete. The current catalog covers 2020 through Aug. 2, 2026; 2026 is year-to-date. Year-specific CSVs remain the source of truth so future collection or reprocessing can happen in manageable batches.

## Rebuild the report

```bash
python3 scripts/build_gilligan_report.py
```

This refreshes the PDF in `output/pdf/` and the derived metrics JSON in `reports/` from the canonical yearly processed CSVs.
