---
name: harmonytime-classes
description: Fetch upcoming Harmony Time classes from the bsport (bsport.io) scheduling API for company 995. Use when asked to query the Harmony Time schedule, upcoming classes, or bsport offers for harmonytime.fr.
---

# Harmony Time Classes

Use the bundled script to fetch upcoming class offers for Harmony Time (company 995).

## Run

- Run `scripts/harmonytime_classes.py` to return upcoming offers as JSON.
- Use `--days N` to set the lookahead window (default: 7; `0` means no end date).
- Use `--limit N` to cap the number of offers returned (default: 50; `0` means no limit).
- Use `--activity <text>` to filter by activity name substring (case-insensitive, repeatable).
- Use `--coach <id>` to filter by coach id (repeatable, matches `coach` or `coach_override`).
- Use `--available-only` to only include offers with `available=true`.
- Use `--raw` to return the full offer objects instead of the reduced schema.
- Use `--pretty` to pretty-print JSON output.

## Output

The script returns JSON with a summary and an `offers` list. By default each offer includes:

- `id`, `company`, `activity_name`, `date_start`, `duration_minute`, `timezone_name`
- `available`, `full`, `effectif`, `validated_booking_count`, `spots_left`
- `establishment`, `coach`, `meta_activity`

## Notes

- Uses `https://api.production.bsport.io/book/v1/offer/` with `company=995` and `ordering=-date_start`.
- Filtering for upcoming dates happens client-side.
- Requires `curl` and network access.
