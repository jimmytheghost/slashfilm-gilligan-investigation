# AGENTS.md

## Project purpose

This repository catalogs SlashFilm stories and tests whether coverage of *Gilligan's Island* and its principal cast is unusually frequent.

## Working rules

1. Preserve source URLs and the publication timestamp shown by SlashFilm for every article.
2. Use the headline as the first-pass source for `subject`; read the article briefly only when the headline is ambiguous.
3. Assign one primary subject per story. Use `notes` for important secondary context.
4. Mark `gilligan_related=yes` only when the story is primarily about *Gilligan's Island*, its franchise, or a principal cast member. Passing mentions are `no`.
5. Keep collection, cleaning, and visualization logic in `scripts/`; do not hand-edit generated charts.
6. Keep raw captures out of Git unless specifically needed for audit or legally permissible. Never commit credentials, cookies, or personal data.
7. Record assumptions and classification changes in documentation or commit messages.
8. Make comparisons fair: use the same date range and article-selection rules for Gilligan, Batman, *Breaking Bad*, and other comparison subjects.

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
