# Plan 01-03 Summary — Big-five loader modules

**Status:** Complete
**Phase:** 01 — Foundation & Data Layer
**Plan:** 03 — Big-five loaders (WHO, WASH, ENSO, demographics, OAG)
**Wave:** 3 (parallel with 01-04)
**Date:** 2026-05-14

## What was built

Five loader modules under `src/mosaic_dashboard/data/`, each following the §4
reference pattern from RESEARCH.md (public function handles path / filter /
empty-state; `@st.cache_data`-decorated private function does the disk read +
schema check; mtime is an explicit cache-key argument):

| Module | Functions | Notes |
|--------|-----------|-------|
| `who.py` | `load_annual(country)`, `load_weekly(country)`, `load_daily(country)` | Three granularities under `WHO/{annual,weekly,daily}/`. Country filter applied after the cached read. |
| `wash.py` | `load(country)` | Single CSV (`WASH_data_Sikder_2023.csv`). |
| `enso.py` | `load_daily()`, `load_weekly()`, `load_monthly()` | **No country argument** — ENSO is a global climate index that applies to all countries simultaneously (Open Question #2 resolution). |
| `demographics.py` | `load_un_wpp(country)`, `load_africa_2000_2023(country)` | Two distinct sources with different schemas; each has its own `REQUIRED_COLUMNS` set. |
| `oag.py` | `load_daily(country)`, `load_weekly(country)`, `load_monthly(country)` | **Documented exception** to single-`country_iso3` rule: keeps both `origin_iso3` and `destination_iso3`. Country filter is bidirectional (matches either side). |

## Decisions honored (D-XX)

- **D-05, D-06:** One module per `processed/` subdir, named loader functions, normalized-column pandas DataFrames returned. Loaders own the rename from upstream column names to canonical.
- **D-07:** ISO3 country identifier throughout. UN WPP and Africa demographics rename `iso_code → country_iso3` inside the cached reader. OAG is the documented exception — keeps both ISO3 columns because flight mobility is intrinsically pairwise.
- **D-08:** Missing country returns an empty DataFrame (no exception on the happy path).
- **D-10, D-13:** Missing subdir → empty + warn; missing expected file → empty + warn (same handling, both logged). Schema mismatch in a *present* expected file raises `SchemaMismatchError` (D-12). Re-confirmed during plan revision.
- **D-12:** All cached readers call `require_columns(df, REQUIRED, dataset=...)` after the `pd.read_csv`. Failure surfaces as a typed exception with dataset name and missing-column set.
- **D-18, D-20:** Each loader has a public/private split — public function computes mtime and dispatches to a private `_read_*_cached(path, mtime)` decorated with `@st.cache_data(show_spinner=False)`. The internal representation can change in Phase 6 without breaking the public API contract.
- **D-19:** Plain pandas CSV reads only. No parquet sidecars, no polars/duckdb backend, no geopandas/fiona/shapely added in Phase 1. Verified by DATA-03 grep (see below).

## Commits

| SHA | Message |
|-----|---------|
| `aaae425` | feat(01-03): implement WHO and WASH loaders |
| `d6bfd96` | feat(01-03): implement ENSO and demographics loaders |
| `3e70b13` | feat(01-03): implement OAG flight-mobility loaders |

## Verification

### DATA-03 — No network imports
```
$ grep -rE '^(from |import )(requests|httpx|urllib\.request|aiohttp)\b' src/mosaic_dashboard/data/
(no matches)
```
✓ DATA-03 OK: no network imports at the data-layer boundary.

### Import smoke test
```
All 12 loader functions importable
```
All public loader signatures present and callable across the five modules.

### Live read test against `~/MOSAIC/MOSAIC-data/processed/`
```
ENSO daily: 80496 rows, cols=['date', 'doy', 'month', 'month_name', 'value', 'variable']
demographics.load_un_wpp(AGO): 134 rows
OAG daily, country=AGO bidirectional: 79 rows
OAG daily, no filter: 1558 rows
```
Loaders read real upstream data, schema validation passes, country filter (including bidirectional OAG) returns expected non-zero rows for AGO.

## Key files created

- `src/mosaic_dashboard/data/who.py`
- `src/mosaic_dashboard/data/wash.py`
- `src/mosaic_dashboard/data/enso.py`
- `src/mosaic_dashboard/data/demographics.py`
- `src/mosaic_dashboard/data/oag.py`

## Cross-plan contract Plan 04 and Plan 05 rely on

- All loaders accept ISO3 country codes (except `enso.load_*` which take none, and OAG which filters bidirectionally).
- All return pandas DataFrame; empty DataFrame on missing subdir / missing file / missing country; `SchemaMismatchError` on column-set mismatch.
- All cached readers keyed on `(path: str, mtime: float)` — Phase 2+ should follow this pattern when adding loaders.

## Recovery note

This plan was originally spawned in a sandboxed worktree agent. Mid-execution
the sandbox blocked further `git add` / `python` commands after Task 1's
commit. ENSO + demographics had already been written to disk (Task 2's source
code); OAG (Task 3) and the SUMMARY were finished by the orchestrator
directly. All three commits live on the worktree branch with the planned
content; live verification passed against the real upstream data root.

## Self-Check: PASSED

- [x] WHO loader: live read returned 29 rows for AGO annual
- [x] WASH loader: live read returned 1 row for AGO
- [x] ENSO loader: live read returned 80,496 rows daily (no country filter)
- [x] demographics loader: live read returned 134 UN WPP rows for AGO
- [x] OAG loader: live read returned 79 rows for AGO bidirectional, 1558 unfiltered
- [x] DATA-03 grep: zero network imports under `src/mosaic_dashboard/data/`
- [x] All 12 public functions importable
- [x] Three atomic commits (one per task)

## must_haves verification

- ✓ D-05 + D-06: Big-five loaders return normalized pandas DataFrames
- ✓ D-10: Missing-subdir / missing-file paths log warning + return empty (manually confirmed via `_resolve_*_csv` branches)
- ✓ D-12 + D-13: require_columns raises SchemaMismatchError on schema mismatch (helper unchanged from Plan 02)
- ✓ D-08: country-not-in-data returns empty DataFrame
- ✓ D-18 + D-20: each loader has public/private split, mtime is explicit cache-key arg
- ✓ D-07: country_iso3 canonical column (except OAG documented exception)
- ✓ D-19: pandas-only, no parquet/polars/duckdb
