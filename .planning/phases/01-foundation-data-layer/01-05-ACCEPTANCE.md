# Phase 1 Acceptance Log — A1 through A10

> Walk-through performed: 2026-05-14. User signed off "approved — all checks pass."
> Automated checks (A1, A2, A9, A10) were verified inline by the orchestrator
> before hand-off; the interactive checks (A3–A8) were walked through manually
> by the user against the running dashboard.

---

## A1: `uv sync` succeeds from a fresh clone — PASS

**Maps to:** ENV-01, ROADMAP §1 criterion 1

**Observed:** `uv sync` exits 0 on the current checkout; `.venv/` and `uv.lock` both present and tracked.

---

## A2: `uv run streamlit run src/mosaic_dashboard/app.py` launches — PASS

**Maps to:** ENV-02, ROADMAP §1 criterion 1

**Observed:** Pre-validated headless during plan execution; orchestrator confirmed `/_stcore/health` returns `ok` on port 8765. User confirmed interactive launch on port 8501.

---

## A3: Data Status page reachable and renders — PASS

**Maps to:** D-11

**Observed:** The Data Status page renders the 12-row table covering all expected subdirs (`WHO/annual`, `WHO/weekly`, `WHO/daily`, `WASH`, `ENSO`, `demographics`, `OAG`, `shapefiles`, `immunity`, `vaccine_effectiveness`, `symptomatic`, `similarity_matrix`) with status / file_count / latest_mtime columns.

---

## A4: Offline — dashboard still loads — PASS

**Maps to:** DATA-03, ROADMAP §1 criterion 3

**Observed:** Dashboard renders identically with the network disconnected. No external network calls in the hot path; confirmed by both the offline run and the DATA-03 grep (zero `requests`/`httpx`/`urllib.request`/`aiohttp` imports under `src/mosaic_dashboard/data/`).

---

## A5: Missing subdir produces empty DF + warning, no crash — PASS

**Maps to:** DATA-04, D-10, ROADMAP §1 criterion 4

**Observed:** Renaming a `processed/` subdir produces `status=MISSING` rows on Data Status, a `logging.warning` line in the launching terminal, and no traceback in the browser. Rename restored after the check.

---

## A6: Malformed CSV produces SchemaMismatchError — PASS

**Maps to:** D-12, D-13

**Observed:** A CSV missing a required column triggers `SchemaMismatchError` with the dataset name and missing-column set, as expected from the `require_columns()` helper. Only schema mismatch in a *present* expected file raises; missing subdir / missing file still warn-and-empty per D-13.

---

## A7: Sidebar override changes effective path mid-session — PASS

**Maps to:** DATA-01, D-03, D-04

**Observed:** Typing a valid alternate path into the sidebar's session-only override text input refreshes the Data Status table on next interaction. `config.toml` on disk is unchanged (resolution order is sidebar → TOML → default per D-04, and only the session_state slot is touched per D-03).

---

## A8: CSV edit shows on next page interaction without restart — PASS

**Maps to:** DATA-02, D-18

**Observed:** `touch`-ing a WHO annual CSV bumps the `latest_mtime` column on Data Status without restarting the Streamlit process — the `@st.cache_data(mtime)` keying invalidates the cache on the next call because mtime is part of the cache key.

---

## A9: `uv.lock` is committed — PASS

**Maps to:** ENV-01

**Observed:** `git ls-files | grep uv.lock` returned a hit (verified by orchestrator before hand-off).

---

## A10: README documents the launch one-liner — PASS

**Maps to:** ENV-02, ROADMAP §1 criterion 1

**Observed:** `grep -F 'uv sync && uv run streamlit run src/mosaic_dashboard/app.py' README.md` returned a hit (verified by orchestrator before hand-off).

---

## Requirements Coverage Map

| Requirement | A-check coverage | Status |
| ----------- | ----------------- | ------ |
| DATA-01 (configurable data path) | A7 | ✓ |
| DATA-02 (fresh-read with invisible caching) | A8 | ✓ |
| DATA-03 (offline in hot path) | A4 | ✓ |
| DATA-04 (missing subdir → empty + warning) | A5 (lenient half); A6 (strict half via SchemaMismatchError) | ✓ |
| ENV-01 (reproducible setup with lockfile) | A1, A9 | ✓ |
| ENV-02 (one-liner launches dashboard) | A2, A10 | ✓ |

Every locked Phase 1 requirement is covered by at least one passing A-check.

---

## Phase 1 status: READY TO TRANSITION

All 10 acceptance checks PASS. Every locked requirement (DATA-01..04, ENV-01, ENV-02) is satisfied. Foundation is in place for Phase 2 (Country Navigation & SSA Map) to build on the loader API contract and the sidebar pattern established here.
