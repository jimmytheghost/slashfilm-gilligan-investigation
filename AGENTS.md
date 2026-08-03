# AGENTS.md

## Project purpose

This repository catalogs SlashFilm stories and tests whether coverage of *Gilligan's Island* and its principal cast is unusually frequent. The initial six-year investigation is complete; preserve its reproducibility while extending it carefully.

## Working rules

1. Treat `data/catalog_processed_<year>.csv` as the canonical working datasets. Keep year-specific files even when creating combined analysis outputs.
2. Preserve source URLs and the publication timestamp shown by SlashFilm for every article.
3. Use the headline as the first-pass source for `subject`; read the article briefly only when the headline is ambiguous.
4. Assign one primary subject per story. Use `notes` for important secondary context.
5. Mark `gilligan_related=yes` only when the story is primarily about *Gilligan's Island*, its franchise, or a principal cast member. Passing mentions are `no`.
6. Keep collection, cleaning, and visualization logic in `scripts/`; do not hand-edit generated charts or the final PDF.
7. Rebuild the packet with `python3 scripts/build_gilligan_report.py` after any data or report-code change; commit the regenerated PDF and `reports/gilligan_report_metrics.json` when they change.
8. Keep raw captures out of Git unless specifically needed for audit or legally permissible. Never commit credentials, cookies, or personal data.
9. Record assumptions and classification changes in documentation or commit messages.
10. Make comparisons fair: use the same date range and article-selection rules for Gilligan, Batman, *Breaking Bad*, and other comparison subjects.

## Canonical schema

The core fields are:

`title,date,subject,gilligan_related`

The working schema also supports:

`url,author,section,published_at,subject_type,notes`

## Verification expectations

Before committing data changes:

- Check for duplicate URLs and duplicate titles.
- Check that dates parse and fall within the stated project scope.
- Check that `gilligan_related` contains only `yes` or `no`.
- Review all Gilligan-positive rows manually.
- Run available tests or validation scripts.

Before committing report changes:

- Rebuild the PDF from the canonical yearly CSVs.
- Check the PDF page count and visually inspect changed pages for clipping, overlap, and chart distortion.
- Keep report prose plainspoken and human-readable; explain what the data shows without claiming it proves traffic, cultural importance, or intent.
