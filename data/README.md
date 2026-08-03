# Data

The canonical article-level datasets are `catalog_processed_<year>.csv` for 2020 through 2026. Together they contain 68,398 stories through Aug. 2, 2026. The columns are:

`title,date,subject,gilligan_related,url,author,section,subject_type,notes`

Keep the yearly files as the source of truth. Combined CSVs and intermediate title-repair files are convenience artifacts, not the inputs for the final report.

Raw captures, if needed for reproducibility, belong under `data/raw/` and are ignored by Git by default. Keep source URLs and publication timestamps in the catalog so each classification can be checked against SlashFilm.
