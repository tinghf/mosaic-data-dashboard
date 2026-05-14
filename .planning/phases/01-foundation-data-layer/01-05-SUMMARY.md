# Plan 01-05 Summary — UI shell + Data Status page + acceptance

**Status:** Complete
**Phase:** 01 — Foundation & Data Layer
**Plan:** 05 — UI shell, Data Status page, A1–A10 acceptance checkpoint
**Wave:** 4
**Date:** 2026-05-14

## What was built

| File | Purpose |
|------|---------|
| `src/mosaic_dashboard/ui/sidebar.py` | Shared `render()` helper called at the top of every page. Renders the session-only data-root override text input (D-03) and writes it into `st.session_state[SESSION_KEY]` so `config.py`'s `resolve_data_root()` picks it up on the next interaction. |
| `src/mosaic_dashboard/app.py` | Streamlit entrypoint. Order: `st.set_page_config` → `tomllib` log-level read → idempotent `configure_logging` → `render_sidebar` → welcome screen. |
| `src/mosaic_dashboard/pages/__init__.py` | Package marker for Streamlit's native `pages/` discovery (D-15). |
| `src/mosaic_dashboard/pages/00_Data_Status.py` | Data Status page — 12-row table over `EXPECTED_SUBDIRS` (3 WHO granularities + 9 other subdirs). Columns: status / file_count / latest_mtime. `st.warning`/`st.info`/`st.error` banners for MISSING/EMPTY/INVALID; metric for `shapefiles.available_countries()` count. |
| `.planning/phases/01-foundation-data-layer/01-05-ACCEPTANCE.md` | A1–A10 acceptance log; PASS for all 10, status set to **READY TO TRANSITION**. |

## Decisions honored (D-XX)

- **D-03:** Sidebar override is ephemeral — writes only to `st.session_state[SESSION_KEY]`, never to `config.toml` on disk. Verified in A7.
- **D-11:** Data Status page enumerates each expected `processed/` subdir with presence / file count / latest mtime — first thing a teammate sees.
- **D-15:** Streamlit native `pages/` directory; `00_Data_Status.py` zero-prefixed for stable sidebar ordering. No third-party page-routing libraries.
- **D-17:** `uv sync && uv run streamlit run src/mosaic_dashboard/app.py` launches the dashboard; documented in README and verified by A2/A10.
- **Critical sidebar pattern (RESEARCH.md §5):** Sidebar widget is rendered by `ui.sidebar.render()` called at the top of every page, NOT once in the entrypoint. The entrypoint-once pattern requires `st.navigation`, which we are not using under D-15. This sets the convention Phase 2's country picker will reuse.

## Commits

| SHA | Message |
|-----|---------|
| `bdbbaee` | feat(01-05): shared sidebar helper + Streamlit entrypoint |
| `88afb3a` | feat(01-05): Data Status page enumerating 12 expected processed/ subdirs |
| `1203445` | docs(01-05): scaffold A1-A10 acceptance log for human verification |
| _(this commit)_ | docs(01-05): record A1-A10 PASS + finalize plan SUMMARY |

## Acceptance results (A1–A10)

All 10 acceptance items PASS. See `01-05-ACCEPTANCE.md` for the full log. Coverage matrix:

| Requirement | A-check coverage | Status |
|-------------|-------------------|--------|
| DATA-01 | A7 | ✓ |
| DATA-02 | A8 | ✓ |
| DATA-03 | A4 | ✓ |
| DATA-04 | A5 (lenient) + A6 (strict) | ✓ |
| ENV-01 | A1, A9 | ✓ |
| ENV-02 | A2, A10 | ✓ |

User signed off "approved — all checks pass" on 2026-05-14.

## Self-Check: PASSED

- [x] Tasks 1 + 2 committed atomically
- [x] Streamlit app launches cleanly (orchestrator pre-validated headless; user confirmed interactive)
- [x] Data Status page renders all 12 expected subdir rows
- [x] Sidebar override is ephemeral (session_state only, never written to config.toml)
- [x] A1–A10 acceptance walked through; all PASS
- [x] Phase 1 status set to READY TO TRANSITION

## must_haves verification

- ✓ D-17: `uv sync && uv run streamlit run src/mosaic_dashboard/app.py` works (A2, A10)
- ✓ D-11 + D-15: Data Status page reachable via native `pages/` sidebar entry (A3)
- ✓ D-03: Ephemeral sidebar override changes effective path mid-session without writing config.toml (A7)
- ✓ Missing subdir → MISSING row + logging.warning, no crash (A5)
- ✓ `config.toml` edits take effect on next interaction (A8 mtime refresh demonstrates the same caching layer)

Phase 1 foundation is in place. Phase 2 (Country Navigation & SSA Map) can build directly on:
- The 10 loader modules under `mosaic_dashboard.data.*` (Plans 03/04)
- `resolve_data_root()` + `SESSION_KEY` for the sidebar pattern
- `shapefiles.available_countries()` to populate the country picker
- The `pages/NN_<name>.py` convention (Phase 2 will add `01_Country.py` and `02_SSA_Map.py` or similar)
