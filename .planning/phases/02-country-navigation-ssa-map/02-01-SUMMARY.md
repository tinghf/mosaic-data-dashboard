---
phase: 02-country-navigation-ssa-map
plan: 01
subsystem: data
tags: [geopandas, folium, streamlit-folium, iso3, country-metadata, session-state, uv]

# Dependency graph
requires:
  - phase: 01-foundation-data-layer
    provides: SESSION_KEY pattern in config.py; shapefiles.available_countries() — the ISO3 set country_metadata is cross-checked against
provides:
  - "Three Phase 2 geo-stack dependencies installed and locked: geopandas, folium, streamlit-folium"
  - "Static ISO3 → display-name lookup module at src/mosaic_dashboard/data/country_metadata.py (54 entries, alphabetical-by-name, Angola first)"
  - "COUNTRY_SESSION_KEY constant in mosaic_dashboard.config — single source of truth for selected ISO3 across sidebar selectbox, map-page click handler, and every Phase 3+ view"
  - "warn_if_drifted_from_shapefiles helper for D-29 startup sanity check (defined here; wired in 02-03)"
affects: [02-02 shapefiles geometry loaders, 02-03 sidebar picker + drift-warning wiring, 02-04 SSA map page click handler, Phase 3+ layer views]

# Tech tracking
tech-stack:
  added:
    - "geopandas 1.1.3 (D-22: geometry-reading library for AFRICA_ADM0 + per-country shapes)"
    - "folium 0.20.0 (D-21: Leaflet-backed map renderer)"
    - "streamlit-folium 0.27.2 (D-21: Streamlit ↔ folium bridge with click-event capture)"
    - "pyogrio 0.12.1 (transitive: geopandas 1.x default IO driver — NOT fiona)"
    - "shapely 2.1.2 (transitive: geometry objects)"
    - "pyproj 3.7.2 (transitive: projections)"
    - "branca 0.8.2 (transitive: folium colormaps + popups)"
    - "xyzservices 2026.3.0 (transitive: tile provider registry — supplies CartoDB Positron)"
  patterns:
    - "Static metadata as a side-module under data/ (not a per-subdir loader): country_metadata coexists with the Phase 1 loaders without violating D-05's spirit"
    - "ISO3 frozenset for O(1) click-handler validation (prevents the documented ESH/-99 leak)"
    - "Caller-supplied iterable for drift checks (warn_if_drifted_from_shapefiles takes the ISO3 set as an argument) — avoids circular import on data/shapefiles"
    - "Session-state slot constants live in config.py mirroring Phase 1's SESSION_KEY (D-32 single-source-of-truth pattern)"

key-files:
  created:
    - "src/mosaic_dashboard/data/country_metadata.py (NEW — 54-entry COUNTRIES tuple, ISO3_SET, iter_countries, name_for, warn_if_drifted_from_shapefiles)"
  modified:
    - "pyproject.toml (dependencies: +geopandas>=1.1,<2.0, +folium>=0.20,<1.0, +streamlit-folium>=0.27,<1.0)"
    - "uv.lock (refreshed by uv add + uv sync)"
    - "src/mosaic_dashboard/config.py (+COUNTRY_SESSION_KEY constant)"

key-decisions:
  - "D-21: folium 0.20.0 + streamlit-folium 0.27.2 — Leaflet stack with mature click-event API"
  - "D-22: geopandas 1.1.3 (with pyogrio 0.12.1 as default driver, NOT fiona); explicit-pinned soft ranges (>=1.1,<2.0) per RESEARCH §"
  - "D-24: hand-curated static ISO3 → name table is the single source of truth — NOT generated from AFRICA_ADM0.dbf, NOT pycountry"
  - "D-25 + D-26 + D-27: tuple order IS picker order; first entry IS first-load default; ships alphabetical-by-name with Angola first"
  - "D-28: minimal columns for v1 (iso3 + name only) — region/population/etc. deferred"
  - "D-29: warn_if_drifted_from_shapefiles defined but NOT called from this module; wiring lives in 02-03 (caller passes the iterable to avoid circular import)"
  - "D-32: COUNTRY_SESSION_KEY = 'selected_country_iso3' in config.py — mirrors Phase 1 SESSION_KEY pattern"
  - "8 name deviations from AFRICA_ADM0.dbf labels documented inline (CAR, ROC, DRC, Eq. Guinea, S. Sudan, eSwatini→Eswatini, STP diacritics)"
  - "Includes MUS/SYC (per-country shapes only); excludes ESH/-99 (AFRICA_ADM0.dbf only) — D-29 drift warning surfaces this divergence at runtime"

patterns-established:
  - "Side module convention under data/: pure static lookups (no I/O) live alongside per-subdir loaders without violating D-05's per-subdir-loader pattern"
  - "name_for(iso3) returns the input for unknown codes (never raises) — safe as a selectbox format_func even during transient mismatch"
  - "Drift-check helpers take the iterable as an argument, not as a module-level import, to keep wiring decisions and circular-import risk out of the metadata module"

requirements-completed: [NAV-01, NAV-02, MAP-01, MAP-02]

# Metrics
duration: ~13min
completed: 2026-05-14
---

# Phase 2 Plan 1: Phase 2 Scaffolding (Deps + ISO3 Lookup + Session Key) Summary

**Geo-stack deps (geopandas 1.1.3, folium 0.20.0, streamlit-folium 0.27.2) added via `uv add`; 54-entry static ISO3 → name lookup module created with `iter_countries`/`name_for`/`ISO3_SET`/`warn_if_drifted_from_shapefiles`; `COUNTRY_SESSION_KEY` constant exported from `config.py` as the single source of truth for selected ISO3.**

## Performance

- **Duration:** ~13 min wall (mostly `uv add` resolution + verification)
- **Started:** 2026-05-14T20:43:44Z
- **Completed:** 2026-05-14T22:23:35Z (calendar wall — agent worked across one date roll)
- **Tasks:** 2
- **Files modified:** 4 (1 created, 3 modified)

## Accomplishments

- `uv add geopandas folium streamlit-folium` succeeds; `pyproject.toml` carries soft pins (`geopandas>=1.1,<2.0`, `folium>=0.20,<1.0`, `streamlit-folium>=0.27,<1.0`) per RESEARCH §"Version pins for pyproject.toml"; `uv.lock` refreshed by `uv sync` after the pin normalization.
- `data/country_metadata.py` exports a 54-entry `COUNTRIES` tuple matching RESEARCH §"country_metadata.py — Full Module File" verbatim, plus the four documented helpers (`iter_countries`, `name_for`, `ISO3_SET`, `warn_if_drifted_from_shapefiles`).
- `config.COUNTRY_SESSION_KEY = "selected_country_iso3"` defined immediately after the Phase 1 `SESSION_KEY` constant; Phase 1 imports (`SESSION_KEY`, `resolve_data_root`, `DEFAULT_DATA_ROOT`) remain intact.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Phase 2 deps via `uv add` and define `COUNTRY_SESSION_KEY`** — `df79648` (feat)
2. **Task 2: Create `country_metadata.py` with 54-entry table + helpers** — `c933fb9` (feat)

## Files Created/Modified

- `pyproject.toml` — added 3 dependencies (geopandas, folium, streamlit-folium) with soft `>=major.minor,<next_major` pins; preserved Phase 1 `streamlit` and `pandas` lines.
- `uv.lock` — refreshed by `uv add geopandas folium streamlit-folium` then `uv sync` after the pin normalization edit.
- `src/mosaic_dashboard/config.py` — added `COUNTRY_SESSION_KEY: str = "selected_country_iso3"` constant immediately after `SESSION_KEY`, with a docstring referencing D-32 and explaining the constant is the single source of truth for selected country across sidebar + map-page click handler + every Phase 3+ layer view.
- `src/mosaic_dashboard/data/country_metadata.py` — new module with the 54-entry `COUNTRIES` tuple (matches RESEARCH §"country_metadata.py — Full Module File" verbatim), `ISO3_SET` frozenset, `iter_countries()` list-copy API, `name_for(iso3)` with safe fallback to input on unknown codes (never raises), and `warn_if_drifted_from_shapefiles(available_iso3s)` startup helper that emits a single `log.warning` on set divergence and never raises (D-29; D-04 spirit).

## Resolved Versions (from `uv.lock`)

| Package | Version | Notes |
|---------|---------|-------|
| geopandas | 1.1.3 | D-22 |
| folium | 0.20.0 | D-21 |
| streamlit-folium | 0.27.2 | D-21 |
| pyogrio | 0.12.1 | transitive — geopandas 1.x default IO driver (NOT fiona) |
| shapely | 2.1.2 | transitive (geopandas) |
| pyproj | 3.7.2 | transitive (geopandas) |
| branca | 0.8.2 | transitive (folium) |
| xyzservices | 2026.3.0 | transitive (folium) — supplies CartoDB Positron tile registry |

## Country Metadata Reference

`COUNTRIES` matches RESEARCH §"country_metadata.py — Full Module File" — 54 entries, alphabetical-by-name with Angola first (D-26, D-27). MUS and SYC are included (per-country shapes exist but neither is in `AFRICA_ADM0.dbf`); ESH and `-99` are excluded (they're in `AFRICA_ADM0.dbf` but no per-country shape exists). Eight name deviations from the DBF text are noted inline: CAR (`Central African Republic`), ROC (`Republic of the Congo`), DRC (`Democratic Republic of the Congo`), GNQ (`Equatorial Guinea`), SSD (`South Sudan`), SWZ (`Eswatini`, ISO 3166 spelling not `eSwatini`), STP with full diacritics (`São Tomé and Príncipe`), and CIV with diacritic preserved (`Côte d'Ivoire`).

`warn_if_drifted_from_shapefiles` is **defined but NOT yet called** — wiring lives in 02-03 (the sidebar will call it once on first render with `shapefiles.available_countries()` per RESEARCH §"Where to call `warn_if_drifted_from_shapefiles()`"). With Phase 1's `available_countries()` returning the 54 per-country ISO3 codes, the expected warning on first launch will read: `in metadata but no shapefile: []; in shapefiles but not metadata: []` (because MUS/SYC HAVE per-country shapes and are in metadata). The ESH/-99 divergence only surfaces when 02-02's `load_africa_geometry()` reads the AFRICA_ADM0.dbf records — the metadata module itself does not interact with that file.

## Decisions Made

- Normalized the `uv add` output to RESEARCH-recommended soft pins (`>=major.minor,<next_major`) instead of accepting `uv`'s default `>=exact-version` pins. Rationale: soft pins documented in RESEARCH §"Version pins for pyproject.toml" let `uv sync` pull patch updates without re-locking; ran `uv sync` after the edit to refresh `uv.lock` so the lock file reflects the final pin set.
- Used the RESEARCH skeleton verbatim for the COUNTRIES tuple (54 entries, alphabetical-by-name, Angola first, 8 inline-noted name deviations). Per D-27 the planner can re-order or rename freely by editing the list — this is the "one knob serves both picker-order and first-load default" pattern (D-26).
- Did NOT call `warn_if_drifted_from_shapefiles` from inside `country_metadata.py` (e.g., at import time). The helper takes the iterable as a function argument; wiring is deferred to 02-03. Rationale per RESEARCH §"Where to call": (a) keeps `country_metadata` import-side-effect-free, (b) avoids a circular import on `data/shapefiles` (which transitively imports `config.resolve_data_root`), (c) lets the planner choose between `app.py` startup and a session-gated sidebar one-shot without editing this module.

## Deviations from Plan

None — the plan was executed exactly as written.

Minor footnote on the Task 1 `<verify>` block: the inline `automated` command read `streamlit_folium.__version__`, but the installed `streamlit_folium 0.27.2` package does not expose `__version__` as a module attribute. The acceptance criteria require only that the three packages import cleanly (and that the constant is exported); both conditions verified via `import streamlit_folium; print('OK')` and `import geopandas, folium; print(geopandas.__version__, folium.__version__)` separately. This is a flaw in the verify recipe rather than the implementation, and does not affect acceptance.

## Issues Encountered

None.

## Threat Surface Scan

No new surface introduced relative to the plan's `<threat_model>`. T-02-01 (supply-chain) is mitigated as planned via `uv.lock` content-addressed hashes (now updated). T-02-02 (tampering of `country_metadata.py`) and T-02-03 (information disclosure) remain as `accept` per the plan — the new module has no PII, no secrets, and no remote-write surface.

## DATA-03 Offline Check

`grep -rE '^(from |import )(requests|httpx|urllib\.request|aiohttp)\b' src/mosaic_dashboard/` returns zero matches — Phase 1's Python-layer offline guarantee is preserved (folium's tile-fetching is a browser-side concern, not a Python-side network call; per RESEARCH §"Offline behavior" this is documented but not in scope for this plan).

## Known Stubs

None. Every helper has a concrete implementation; nothing renders to the UI in this plan (UI wiring lives in 02-03).

## User Setup Required

None — no external services, no env vars, no secrets.

## Next Phase Readiness

Plans 02-02, 02-03, and 02-04 can all import from these artifacts immediately:

- `from mosaic_dashboard.config import COUNTRY_SESSION_KEY` — for 02-03's sidebar selectbox `key=` binding and 02-04's click-handler write.
- `from mosaic_dashboard.data import country_metadata` — for 02-03's selectbox options (`iter_countries`) and `format_func` (`name_for`), 02-04's click-handler validation (`ISO3_SET`), and 02-03's startup drift warning (`warn_if_drifted_from_shapefiles`).
- `geopandas`, `folium`, `streamlit_folium` — for 02-02's `load_africa_geometry()` / `load_country_geometry()` (geopandas) and 02-04's `st_folium()` map render.

No blockers for the rest of the Phase 2 wave.

## Self-Check: PASSED

Verified post-write:
- FOUND: `src/mosaic_dashboard/data/country_metadata.py` (54-entry COUNTRIES tuple, 4 helpers exported)
- FOUND: `src/mosaic_dashboard/config.py` carries `COUNTRY_SESSION_KEY = "selected_country_iso3"`
- FOUND: `pyproject.toml` `[project.dependencies]` lists `geopandas`, `folium`, `streamlit-folium` with soft pins
- FOUND: `uv.lock` updated (resolved versions: geopandas 1.1.3, folium 0.20.0, streamlit-folium 0.27.2)
- FOUND: commit `df79648` (Task 1: deps + COUNTRY_SESSION_KEY)
- FOUND: commit `c933fb9` (Task 2: country_metadata.py)
- PLAN-LEVEL VERIFY: `uv run python -c "from mosaic_dashboard.config import COUNTRY_SESSION_KEY; from mosaic_dashboard.data import country_metadata; assert len(country_metadata.iter_countries()) == 54"` exits 0.
- DATA-03 OFFLINE GUARANTEE: preserved (no new HTTP-client imports under `src/mosaic_dashboard/`).

---
*Phase: 02-country-navigation-ssa-map*
*Completed: 2026-05-14*
