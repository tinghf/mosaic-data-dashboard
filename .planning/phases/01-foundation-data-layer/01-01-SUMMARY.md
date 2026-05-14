---
phase: 01-foundation-data-layer
plan: 01
subsystem: scaffolding
tags: [uv, python, streamlit, pandas, packaging, src-layout, project-conventions]

requires:
  - phase: 00-pre-phase
    provides: ".planning/PROJECT.md, .planning/REQUIREMENTS.md, .planning/ROADMAP.md (greenfield repo state — only .planning/ and .git/ existed at start)"
provides:
  - "Installable mosaic-dashboard package at src/mosaic_dashboard/ (uv-managed, importable via uv run)"
  - "Committed uv.lock pinning the full dependency graph for reproducible installs (ENV-01)"
  - "Documented launch one-liner in README: uv sync && uv run streamlit run src/mosaic_dashboard/app.py (ENV-02)"
  - "Repo-root config.toml with [data] root default and [logging] level — feeds Plan 02's config resolver"
  - "CLAUDE.md locking project conventions (uv-only, READ-ONLY data, ISO3 canonical, native pages/ pattern)"
  - "COLUMN_DISCOVERY.md — ground-truth upstream CSV column names per processed/ subdir for Plans 03/04 loader required_columns sets"
affects:
  - "Plan 01-02 (foundation modules: config.py, logging_config.py, errors.py, _schema.py) — depends on pyproject + uv.lock"
  - "Plan 01-03 (per-subdir loaders) — depends on COLUMN_DISCOVERY.md for required_columns + rename maps"
  - "Plan 01-04 (shapefiles + static layers) — depends on COLUMN_DISCOVERY.md (ADM0 ISO3 prefixes, similarity_matrix space-delimited shape)"
  - "Plan 01-05 (app.py entry + Data Status page) — depends on installable package and config.toml"
  - "All Phase 2+ work — every later phase uses the launch one-liner and inherits CLAUDE.md conventions"

tech-stack:
  added:
    - "uv 0.8.2 (package manager + lockfile)"
    - "streamlit 1.57.0 (transitive: pyarrow, pydeck, watchdog, ...)"
    - "pandas 3.0.3 (transitive: numpy 2.4.4)"
    - "uv_build >=0.8.2,<0.9.0 (build backend, written by uv init --package)"
  patterns:
    - "src/ layout with installable package (D-14, D-16)"
    - "PEP 621 metadata in pyproject.toml managed by uv (no setup.py, no requirements.txt)"
    - "Repo-root config.toml for app-owned config; .streamlit/config.toml reserved for Streamlit runtime (P4 mitigation, never created)"
    - "Two-digit zero-padded prefix convention for future pages/NN_*.py (P1 prevention, documented in CLAUDE.md)"

key-files:
  created:
    - "pyproject.toml — PEP 621 metadata + streamlit/pandas deps + uv_build backend"
    - "uv.lock — pinned dependency graph (1124 lines, 45 packages resolved)"
    - "src/mosaic_dashboard/__init__.py — package marker with main() shim from uv init"
    - ".python-version — pins 3.13"
    - ".gitignore — excludes .venv/, __pycache__, .pytest_cache, build artifacts, .streamlit/secrets.toml"
    - "README.md — quickstart + data-path-resolution + project-layout sections"
    - "CLAUDE.md — four project conventions (uv run only, READ-ONLY data, ISO3 canonical, pages/ pattern)"
    - "config.toml — [data] root default + [logging] level + P4-mitigation header comment"
    - ".planning/phases/01-foundation-data-layer/COLUMN_DISCOVERY.md — 12 subdir sections + read-only verification"
  modified: []

key-decisions:
  - "Pinned uv_build to >=0.8.2,<0.9.0 (deviation from RESEARCH.md which specified >=0.11.14,<0.12) — local uv 0.8.2 writes this version, and upgrading uv was not in scope; uv.lock still hash-verifies the dep graph (T-01-03 mitigation preserved)"
  - "Used uv add to set dependency ranges, then hand-tightened to streamlit>=1.57,<2.0 and pandas>=3.0,<4.0 per RESEARCH.md §Standard Stack — uv.lock pins exact 1.57.0 / 3.0.3"
  - "Kept project.scripts shim (mosaic-dashboard = 'mosaic_dashboard:main') auto-created by uv init — harmless and matches the resulting pyproject.toml shape documented in RESEARCH.md"
  - "Discovered similarity_matrix CSV is space-delimited (not comma) — Plan 04 will need pd.read_csv(sep=r'\\s+') or sep=' ', flagged in COLUMN_DISCOVERY.md"
  - "OAG has two ISO3 columns (origin_iso3 + destination_iso3) — Plan 03 OAG loader is the lone exception to single-country_iso3 rename rule, flagged in COLUMN_DISCOVERY.md and consistent with RESEARCH.md §Open-Questions Item 2 resolution"
  - "immunity/, vaccine_effectiveness/, symptomatic/ are global (no country column) — their loaders' country parameter will be ignored or used only for metadata filtering, flagged in COLUMN_DISCOVERY.md"

patterns-established:
  - "Per-task atomic commits with conventional-commit prefixes scoped to the plan (feat(01-01): ..., docs(01-01): ...)"
  - "Auto-discovered uv init structure left intact (src/<pkg>/__init__.py with main()) — downstream plans add files alongside, not in place of"
  - "Read-only verification for upstream-data-touching tasks: capture mtime hash before/after with sorted find input for determinism"

requirements-completed: [ENV-01, ENV-02]

duration: 7min
completed: 2026-05-14
---

# Phase 01 Plan 01: Project Scaffold + Column Discovery Summary

**Stood up an installable mosaic-dashboard uv package with pinned lockfile, locked project conventions in CLAUDE.md, and discovered verbatim upstream CSV columns for all 12 processed/ subdir patterns — Plans 02-05 can now build against a known, reproducible foundation.**

## Performance

- **Duration:** ~7 min
- **Started:** 2026-05-14T06:42Z (approx, from worktree branch creation)
- **Completed:** 2026-05-14T06:50Z
- **Tasks:** 3/3
- **Files created:** 9
- **Files modified:** 0

## Accomplishments

- **ENV-01 satisfied** — `pyproject.toml` ships PEP 621 metadata + streamlit/pandas deps + uv_build backend; `uv.lock` is committed (45 packages resolved) and `uv sync` exits 0 from a clean state.
- **ENV-02 satisfied** — README documents the exact launch one-liner `uv sync && uv run streamlit run src/mosaic_dashboard/app.py` with three-level data-path resolution explained.
- **Project conventions locked for all downstream agents** — CLAUDE.md captures the four hard constraints from RESEARCH.md §Open-Questions Item 5: `uv run` only, `~/MOSAIC/MOSAIC-data/` is READ-ONLY, ISO3 canonical, `pages/` native (no third-party routing libs).
- **Upstream column ground truth captured** — COLUMN_DISCOVERY.md has 12 subdir sections + read-only verification, with `required_columns` recommendations, country/date column maps, and three flagged exceptions (OAG dual-ISO3, similarity_matrix space-delimited, global-no-country layers) that would otherwise have surfaced as mid-implementation surprises in Plans 03/04.

## Task Commits

Each task was committed atomically on `worktree-agent-ab6f7b500a11c415f`:

1. **Task 1: Initialize uv package and install runtime dependencies** — `192d04d` (feat)
2. **Task 2: Author config.toml, README, and CLAUDE.md** — `79e785e` (docs)
3. **Task 3: Discover and record upstream CSV column names** — `cce3006` (docs)

Plan metadata commit (this SUMMARY.md) is added separately by the post-plan worktree commit step.

## Files Created/Modified

**Created (9 files):**

- `pyproject.toml` — PEP 621 project metadata, streamlit/pandas deps, uv_build backend
- `uv.lock` — Pinned dependency graph (45 packages)
- `src/mosaic_dashboard/__init__.py` — Package marker with `main()` shim
- `.python-version` — Pins Python 3.13
- `.gitignore` — Excludes `.venv/`, `__pycache__`, pytest/mypy/ruff caches, build artifacts, `.streamlit/secrets.toml`
- `README.md` — Quickstart, data-path-resolution, project-layout
- `CLAUDE.md` — Four locked conventions for downstream agents
- `config.toml` — Repo-root app config with `[data] root` + `[logging] level`
- `.planning/phases/01-foundation-data-layer/COLUMN_DISCOVERY.md` — Per-subdir upstream-column reference

**Modified:** None — greenfield plan, all files newly created.

## Final pyproject.toml shape (for downstream reference)

```toml
[project]
name = "mosaic-dashboard"
version = "0.1.0"
description = "Local Streamlit dashboard for the MOSAIC processed-data inspector"
readme = "README.md"
authors = [{ name = "Tony Ting", email = "tony.ting@gatesfoundation.org" }]
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.57,<2.0",
    "pandas>=3.0,<4.0",
]

[project.scripts]
mosaic-dashboard = "mosaic_dashboard:main"

[build-system]
requires = ["uv_build>=0.8.2,<0.9.0"]
build-backend = "uv_build"
```

Resolved versions pinned by `uv.lock`: streamlit 1.57.0, pandas 3.0.3, numpy 2.4.4, pyarrow 24.0.0.

## Upstream column discovery — at-a-glance map

Full details in [`COLUMN_DISCOVERY.md`](./COLUMN_DISCOVERY.md). One-line per subdir:

| Subdir | Primary file | Country col (→ canonical) | Date col | Notes |
|--------|-------------|---------------------------|----------|-------|
| `WHO/annual` | `who_afro_annual_1949_2024.csv` | `iso_code` → `country_iso3` | `year` (int) | 5 files; primary covers 1949–2024 |
| `WHO/weekly` | `cholera_country_weekly_processed.csv` | `iso_code` → `country_iso3` | `date_start` (parse_dates) | Plus 68 MB suitability variant |
| `WHO/daily` | `cholera_country_daily_processed.csv` | `iso_code` → `country_iso3` | `date` (parse_dates) | `month` / `week` are quoted strings |
| `WASH` | `WASH_data_Sikder_2023.csv` | `iso_code` → `country_iso3` | none (2023 snapshot) | Mixed-case cols (Piped_Water, ...) |
| `ENSO` (3 files) | `compiled_ENSO_1970_2025_{daily,weekly,monthly}.csv` | **none — global** | varies (`date` or `date_start`) | Long-format (variable + value); 4 indices |
| `demographics` | `UN_world_population_prospects_1967_2100.csv` + `demographics_africa_2000_2023.csv` | `iso_code` → `country_iso3` | year (int) | Two distinct sources, different column shapes |
| `OAG` (3 files) | `oag_africa_2017_mean_{daily,weekly,monthly}.csv` | **two ISO3 cols** (origin/destination) | none (2017 mean) | Single-year mean flow; bidirectional filter |
| `shapefiles` | 55 ADM0 shapefiles (1 regional + 54 ISO3) | filename prefix → ISO3 | none (static) | Geopandas deferred to Phase 2 |
| `immunity` | `immune_{decay,durability}_data.csv` | **none — global** | none (`day` offset) | Effectiveness vs. days post-vax |
| `vaccine_effectiveness` | `vaccine_effectiveness_data.csv` | **none — global** | none (`day` offset) | `day` can be float (93.5) |
| `symptomatic` | `summary_symptomatic_cases.csv` | **none — global** | none (publication `year`) | Review-paper estimates |
| `similarity_matrix` | `similarity_matrix_africa.csv` | ISO3 in index + columns | none (static) | **Space-delimited 51×51 matrix** (not CSV) |

## Decisions Made

- **uv_build version pin** — RESEARCH.md specified `uv_build>=0.11.14,<0.12` (matches PyPI latest uv 0.11.14), but the locally-installed uv is 0.8.2 which writes `uv_build>=0.8.2,<0.9.0`. Kept the 0.8.x range — it builds successfully and uv.lock still hash-verifies. Upgrading uv would have been an out-of-scope side quest; T-01-03 mitigation (hash-verified installs via uv.lock) is preserved.
- **Hand-tightened dependency ranges** — uv add wrote `streamlit>=1.57.0` and `pandas>=3.0.3` (no upper bound). Updated to `streamlit>=1.57,<2.0` and `pandas>=3.0,<4.0` per RESEARCH.md §Standard Stack to prevent surprise major-version drift on a future `uv sync`.
- **Kept the `[project.scripts]` shim** — `uv init --package` auto-created `mosaic-dashboard = "mosaic_dashboard:main"` and a `main()` in `__init__.py`. RESEARCH.md said this could be omitted or stubbed; left intact since it's harmless and matches the published scaffold shape (deferring a tidy-up to whichever later plan formally introduces a CLI shim, if any).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `requires-python` mismatch between `uv init` output and plan acceptance criterion**

- **Found during:** Task 1
- **Issue:** `uv init --package --python 3.13` wrote `requires-python = ">=3.13"` to pyproject.toml. The plan's acceptance criterion explicitly required `requires-python = ">=3.11"` (matching the `requires-python = ">=3.11"` from RESEARCH.md §Project-Scaffolding "Resulting pyproject.toml shape"). Without correcting it, Task 1 verification would have failed and downstream teammates on Python 3.11 / 3.12 environments would have been locked out.
- **Fix:** Edited pyproject.toml to set `requires-python = ">=3.11"` and re-ran `uv sync` to verify the lockfile remained valid. Exit 0.
- **Files modified:** `pyproject.toml`
- **Verification:** `grep -q 'requires-python = ">=3.11"' pyproject.toml` returns 0; `uv sync` exits 0; plan-level verification step 2 (`import streamlit`) still passes.
- **Committed in:** `192d04d` (rolled into Task 1 commit)

**2. [Rule 3 - Blocking] `uv_build` version pin mismatch between local uv version and RESEARCH.md spec**

- **Found during:** Task 1 (post-`uv init`)
- **Issue:** RESEARCH.md §Project-Scaffolding specifies `requires = ["uv_build>=0.11.14,<0.12"]`. Local uv is 0.8.2 (RESEARCH.md §Tooling table noted this gap and flagged "planner may want a uv self update step"). `uv init --package` writes `uv_build>=0.8.2,<0.9.0` to match the resolver's installed version. Forcing `>=0.11.14` would have caused `uv sync` to fail.
- **Fix:** Kept the uv-written `uv_build>=0.8.2,<0.9.0` pin. The plan's acceptance criterion only requires `grep -q "uv_build" pyproject.toml` (i.e., it's the *backend* that matters, not a specific version range). uv.lock still hash-pins the dep graph (T-01-03 mitigation intact). Logged as a deliberate deviation here.
- **Files modified:** `pyproject.toml` (kept uv-default value rather than overriding)
- **Verification:** `uv sync` exits 0; `grep -q "uv_build" pyproject.toml` passes.
- **Committed in:** `192d04d` (rolled into Task 1 commit)

**3. [Rule 1 - Bug] Pre-flight read-only verification used unstable mtime hash baseline**

- **Found during:** Task 3 (post-write verification of upstream read-only contract)
- **Issue:** First baseline computed via `find ~/MOSAIC/.../*.csv -printf "%T@ %p\n" | md5sum` (no sort). `find` traversal order is non-deterministic across runs, so the post-task hash differed from the baseline even though no files were modified — falsely flagging the read-only contract as violated.
- **Fix:** Added `| sort` to make the hash deterministic, re-verified upstream files unchanged (stable hash `1a473661099f6a9059b51469b6053b0a`), and documented the corrected verification in COLUMN_DISCOVERY.md's "Read-only verification" section. Underlying file mtimes confirmed at `1770940938+` (2026-02-12) — well before this session, unchanged.
- **Files modified:** `.planning/phases/01-foundation-data-layer/COLUMN_DISCOVERY.md` (only the verification footer; column data unaffected)
- **Verification:** Spot-checked mtimes of two CSVs (`who_afro_annual_1949_2024.csv`, `WASH_data_Sikder_2023.csv`) — both still at the pre-session timestamp. `git status` on the worktree shows no upstream paths touched.
- **Committed in:** `cce3006` (rolled into Task 3 commit)

## Known Stubs

None. All files created in this plan are complete artifacts: pyproject.toml is a working PEP 621 config, uv.lock is fully resolved, CLAUDE.md/README/config.toml are final, COLUMN_DISCOVERY.md is the ground-truth reference for Plans 03/04. The `src/mosaic_dashboard/__init__.py` ships `uv init`'s default `main()` stub — this is the expected starter shape for an installable uv package; Plan 01-05 will replace it with the real entry-point implementation, and the existing `[project.scripts]` shim continues to point at a callable in the interim.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: build-backend-version-skew | `pyproject.toml` | `uv_build>=0.8.2,<0.9.0` is older than RESEARCH.md's recommended `>=0.11.14,<0.12`. T-01-03 disposition was `mitigate`; chose to retain the 0.8.x range and rely on `uv.lock` hash verification instead of forcing a uv self-update. Surface for review by the verifier — if a uv 0.11.x upgrade is desired, it should be a separate plan, not buried here. |

## Self-Check: PASSED

Verified all claimed artifacts and commits exist:

- `pyproject.toml` — FOUND (lines 1-21)
- `uv.lock` — FOUND (218125 bytes)
- `src/mosaic_dashboard/__init__.py` — FOUND
- `.python-version` — FOUND (contains `3.13`)
- `.gitignore` — FOUND (contains `.venv/`)
- `README.md` — FOUND (contains launch one-liner)
- `CLAUDE.md` — FOUND (contains ISO3 + READ-ONLY language)
- `config.toml` — FOUND (parses via tomllib)
- `.planning/phases/01-foundation-data-layer/COLUMN_DISCOVERY.md` — FOUND (13 `^##` sections)
- Commit `192d04d` (Task 1) — FOUND in `git log`
- Commit `79e785e` (Task 2) — FOUND in `git log`
- Commit `cce3006` (Task 3) — FOUND in `git log`

Plan-level verification steps 1-4 all pass (uv sync exit 0, imports succeed, config.toml parses, ≥12 sections).
