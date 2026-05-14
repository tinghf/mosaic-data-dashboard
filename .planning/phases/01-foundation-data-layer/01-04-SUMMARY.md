# Plan 01-04 Summary — Small-five loader modules

**Status:** Complete
**Phase:** 01 — Foundation & Data Layer
**Plan:** 04 — Small-five loaders (shapefiles + immunity + vaccine_effectiveness + symptomatic + similarity_matrix)
**Wave:** 3 (parallel with 01-03)
**Date:** 2026-05-14

## What was built

Five loader modules under `src/mosaic_dashboard/data/`. The shapefiles loader
is **fully implemented** (Plan 05's Data Status page calls it immediately to
confirm shapefile presence). The other four are **stub-with-discovery** —
full public API surface is locked here so Plans 02–07 can import and call
these functions; the visualization-specific reshape will be finished in
Phase 5.

| Module | Functions | Phase 1 implementation |
|--------|-----------|------------------------|
| `shapefiles.py` | `available_countries()`, `load_africa()`, `load_country(country)` | **Full** — Path-only enumeration; no geopandas dependency added (D-19). |
| `immunity.py` | `load_decay(country)`, `load_durability(country)` | Stub-with-discovery — `country` is API-contract placeholder (data is global per source). |
| `vaccine_effectiveness.py` | `load(country)` | Stub-with-discovery — same global-data caveat as immunity. |
| `symptomatic.py` | `load(country)` | Stub-with-discovery — upstream `location` is mostly NA. |
| `similarity_matrix.py` | `load(country)` | Stub-with-discovery — reads space-delimited 51×51 ISO3 matrix; row filter implemented. |

## Decisions honored (D-XX)

- **D-05, D-06:** One module per `processed/` subdir, named loader functions, normalized-column DataFrames.
- **D-07:** ISO3 country identifier throughout. `shapefiles.available_countries()` returns ISO3 codes parsed from `XXX_ADM0.shp` filenames; `similarity_matrix` uses ISO3 as both index and column names.
- **D-08:** Missing country (e.g., `load_country('ZZZ')`) returns the structurally-correct DataFrame with `exists=False` rows or empty DataFrame, no exception.
- **D-09:** No `Dataset` wrapper class — loaders return raw pandas DataFrames.
- **D-10, D-13:** Missing subdir / missing expected file both warn + empty; only schema mismatch in a *present* file raises.
- **D-12:** `require_columns()` called inside each cached reader; raises `SchemaMismatchError` on column-set mismatch (no-op for similarity_matrix in Phase 1 since the shape isn't a column-set contract).
- **D-18, D-20:** Public/private split with `@st.cache_data(mtime)` on the cached reader. The stubs use the same pattern as the big-five — Phase 5 can change internal representation without touching the public API.
- **D-19:** **No geopandas, fiona, shapely, or pyproj dependency** added in Phase 1. Phase 2's MAP work will introduce the geo stack. Verified by inline grep below.

## Commits

| SHA | Message |
|-----|---------|
| `7773e95` | feat(01-04): implement shapefiles loader (Path-only, no geopandas) |
| `d2df6b1` | feat(01-04): stub immunity/vaccine_effectiveness/symptomatic loaders |
| `a868e8e` | feat(01-04): stub similarity_matrix loader |

## Verification

### DATA-03 — No network imports
```
$ grep -rE '^(from |import )(requests|httpx|urllib\.request|aiohttp)\b' src/mosaic_dashboard/data/
(no matches)
```
✓ DATA-03 OK.

### D-19 — No geo dependency
```
$ grep -rE '^(from |import )(geopandas|fiona|shapely|pyproj)\b' src/mosaic_dashboard/data/
(no matches)
```
✓ D-19 OK.

### Import smoke test
```
All 8 small-five loader functions importable
```

### Live read test against `~/MOSAIC/MOSAIC-data/processed/`
```
available_countries: 54 ISO3 codes — first 5: ['AGO', 'BDI', 'BEN', 'BFA', 'BWA']
shapefiles.load_africa: 4 rows, all exist=True
shapefiles.load_country(AGO): 4 rows, all exist=True
shapefiles.load_country(ZZZ): 4 rows, any exist=False
immunity.load_decay: 3 rows
vaccine_effectiveness.load: 5 rows
symptomatic.load: 9 rows
similarity_matrix.load(): (51, 51) (rows, cols)
similarity_matrix.load(AGO): (1, 51)
```

- 54 countries discovered (matches the 54 country-specific shapefiles, after excluding the SSA-wide `AFRICA_ADM0`).
- `load_country('ZZZ')` correctly returns all-False rows (Phase 1 empty-state behavior).
- `similarity_matrix.load('AGO')` returns the 1-row filtered slice as expected.

## Key files created

- `src/mosaic_dashboard/data/shapefiles.py`
- `src/mosaic_dashboard/data/immunity.py`
- `src/mosaic_dashboard/data/vaccine_effectiveness.py`
- `src/mosaic_dashboard/data/symptomatic.py`
- `src/mosaic_dashboard/data/similarity_matrix.py`

## Phase 5 hand-off (for the developer flesh-out)

Each stub has a stable signature; flesh-out work is internal:

- `immunity`: add a `source` filter if a country-scoped view is desired; the upstream data is global per study.
- `vaccine_effectiveness`: same — global decay curve. `country` argument may become a metadata filter.
- `symptomatic`: upstream `location` is mostly NA; filter by available `location` values where present.
- `similarity_matrix`: decide the final return shape for `country != None` — single row, row+column, or pivoted long-form. The current 1-row return is a reasonable default.

## Recovery note

This plan was originally spawned in a sandboxed worktree agent. Mid-execution
the agent process was killed by a transient Cloudflare 522 API error after
writing `shapefiles.py` (uncommitted). The remaining four stub loaders and
SUMMARY were finished by the orchestrator directly. All three commits live
on the worktree branch with the planned content; live verification passed
against the real upstream data root.

## Self-Check: PASSED

- [x] shapefiles loader: 54 ISO3 codes discovered, AFRICA filtered out, metadata rows correct
- [x] shapefiles empty-state: `load_country('ZZZ')` returns all-False rows
- [x] immunity / vaccine_effectiveness / symptomatic stubs: live-read returns expected small row counts
- [x] similarity_matrix: 51×51 matrix loads from space-delimited CSV; row filter returns 1×51
- [x] DATA-03 grep: zero network imports
- [x] D-19 grep: zero geo-stack imports
- [x] All 8 public functions importable
- [x] Three atomic commits

## must_haves verification

- ✓ D-05 + D-08 + D-10: Each small-five loader returns a pandas DataFrame, handles missing-subdir/country with empty
- ✓ D-06 + D-07 + D-12 + D-18: `resolve_data_root()` + `require_columns()` + `@st.cache_data(mtime)` pattern (similarity_matrix opts out of column-set check per Phase 1 stub note)
- ✓ D-07: `shapefiles.available_countries()` returns ISO3 strings parsed from `XXX_ADM0.shp`
- ✓ D-20: Phase 5 can flesh out the four "stub-with-discovery" loaders without changing the public API
- ✓ D-19: No geopandas / fiona / shapely / pyproj dependency added in Phase 1
