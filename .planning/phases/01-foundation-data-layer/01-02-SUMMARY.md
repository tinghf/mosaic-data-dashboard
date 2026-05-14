---
phase: 01-foundation-data-layer
plan: 02
subsystem: foundation
tags: [config, schema, logging, exceptions, tomllib, streamlit-session-state]

# Dependency graph
requires:
  - phase: 01-foundation-data-layer
    provides: "Plan 01-01 — src/ layout, pyproject.toml with streamlit+pandas deps, uv.lock, repo-root config.toml with [data] root, src/mosaic_dashboard/__init__.py, CLAUDE.md conventions"
provides:
  - "DataLayerError + SchemaMismatchError typed exception hierarchy (D-09)"
  - "require_columns(df, required, dataset) helper raising SchemaMismatchError on missing cols (D-12); tolerates extras (D-13)"
  - "Idempotent configure() for the 'mosaic_dashboard' stdlib logger namespace; safe across Streamlit reruns"
  - "resolve_data_root() implementing D-04 three-tier order: sidebar session override -> config.toml -> default"
  - "Exposed constants for downstream code: SESSION_KEY ('data_root_override'), DEFAULT_DATA_ROOT, CONFIG_TOML_PATH"
  - "src/mosaic_dashboard/data/ and src/mosaic_dashboard/ui/ subpackages scaffolded"
affects: ["01-03 (per-subdir loaders consume require_columns, resolve_data_root, logging)", "01-04 (shapefile loader consumes same primitives)", "01-05 (Data Status page + ui/sidebar.py consume SESSION_KEY, resolve_data_root, configure)", "Phase 2+ country picker reuses the SESSION_KEY pattern in ui/sidebar.py"]

# Tech tracking
tech-stack:
  added: []  # no new deps — uses only stdlib (tomllib, logging, sys, pathlib) + already-installed streamlit/pandas
  patterns:
    - "Typed exception hierarchy under DataLayerError for the data layer (D-09)"
    - "Set-difference column check (set(required) - set(df.columns)) — no pandera"
    - "Module-level _CONFIGURED flag + defensive StreamHandler check for idempotent logging under Streamlit reruns"
    - "Path(__file__).resolve().parents[2] / 'config.toml' for repo-root anchoring from src/ layout"
    - "Sidebar override stored in st.session_state[SESSION_KEY]; empty string == no override (falls through to config.toml)"
    - "resolve_data_root() intentionally NOT cached — TOML reads cheap, config edits take effect on next rerun"

key-files:
  created:
    - "src/mosaic_dashboard/data/__init__.py"
    - "src/mosaic_dashboard/data/errors.py"
    - "src/mosaic_dashboard/data/_schema.py"
    - "src/mosaic_dashboard/logging_config.py"
    - "src/mosaic_dashboard/config.py"
    - "src/mosaic_dashboard/ui/__init__.py"
  modified: []

key-decisions:
  - "Exception hierarchy capped at two classes per D-09 (DataLayerError -> SchemaMismatchError) — no Dataset wrapper, no DataTypeMismatchError sibling in Phase 1"
  - "Logging idempotence uses module-level _CONFIGURED flag plus defensive 'StreamHandler already attached' check — belt-and-suspenders against Streamlit reruns and module hot-reload"
  - "Module-name 'config.py' (not 'config_resolver.py' or similar) matches RESEARCH.md skeleton and Plan 05 import surface"
  - "Empty-string override in st.session_state is treated as 'no override' (falls through) — preserves D-04 semantics when sidebar text input is cleared"
  - "resolve_data_root() does not validate path existence (deferred to Data Status page in Plan 05)"

patterns-established:
  - "Pattern: Loaders import `from mosaic_dashboard.config import resolve_data_root` and `from mosaic_dashboard.data._schema import require_columns`"
  - "Pattern: All loaders log via `logging.getLogger(__name__)` (child of 'mosaic_dashboard') — terminal-only output; UI surfaces use st.warning() instead"
  - "Pattern: Plan 05 sidebar will import `from mosaic_dashboard.config import SESSION_KEY` and bind a text_input widget's `key` to it"
  - "Pattern: Phase 2+ shared sidebar widgets (country picker, etc.) will follow the same SESSION_KEY-in-config-module convention"

requirements-completed: [DATA-01, DATA-04]

# Metrics
duration: 2min
completed: 2026-05-13
---

# Phase 1 Plan 2: Foundation Modules Summary

**Typed `SchemaMismatchError` + `require_columns()` helper, idempotent stdlib logging for the `mosaic_dashboard` namespace, and `resolve_data_root()` with D-04 three-tier resolution (sidebar override -> config.toml -> default).**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-05-14T06:53:51Z
- **Completed:** 2026-05-14T06:55:54Z
- **Tasks:** 3
- **Files created:** 6
- **Files modified:** 0

## Accomplishments

- Two-class exception hierarchy (`DataLayerError` -> `SchemaMismatchError`) with dataset name and missing-column set carried on the exception per D-12, ready for every loader's `require_columns()` call in Plans 03/04.
- `require_columns(df, required, dataset)` set-difference check — tolerates extras silently (D-13), raises with a useful message containing dataset name and sorted missing-column list when any required column is absent.
- Idempotent `configure(level)` for stdlib logging: the `mosaic_dashboard` named logger gets a single `StreamHandler(sys.stderr)` with a uniform formatter, `propagate=False` to stay off the root logger, and a `_CONFIGURED` guard so Streamlit reruns and repeat calls from multiple pages never duplicate handlers.
- `resolve_data_root()` implements D-04 exactly: session-state override (non-empty string) -> repo-root `config.toml` `[data].root` (after `.strip()`) -> default `~/MOSAIC/MOSAIC-data/processed/`. Both override and config values are `expanduser()`'d. Function is NOT cached — TOML reads are cheap and config-file edits should take effect on the next rerun.
- `SESSION_KEY = "data_root_override"`, `DEFAULT_DATA_ROOT`, and `CONFIG_TOML_PATH` exported as module constants so Plan 05's sidebar widget can bind to the slot without redefining it.
- `data/` and `ui/` subpackages scaffolded with package-marker `__init__.py` files. Plan 05 lands `ui/sidebar.py` without further scaffolding.

## Task Commits

Each task was committed atomically:

1. **Task 1: Data layer errors and require_columns helper** — `c13da32` (feat)
2. **Task 2: Idempotent logging configuration** — `9ff40ce` (feat)
3. **Task 3: resolve_data_root + ui package marker** — `363c663` (feat)

## Files Created/Modified

- `src/mosaic_dashboard/data/__init__.py` — Package marker for the `data` subpackage.
- `src/mosaic_dashboard/data/errors.py` — `DataLayerError` base + `SchemaMismatchError(dataset, missing, present=None)` with attributes `.dataset`, `.missing` (set), `.present` (set, empty if not provided). Message format: `"Schema mismatch in dataset '{dataset}': missing required columns {col1, col2, ...}"` with sorted column names.
- `src/mosaic_dashboard/data/_schema.py` — `require_columns(df: pd.DataFrame, required: Iterable[str], dataset: str) -> None`. Set-difference check; raises `SchemaMismatchError(dataset, missing, present=set(df.columns))` on failure; tolerates extras silently.
- `src/mosaic_dashboard/logging_config.py` — `configure(level: str = "INFO") -> None`. Module-level `_CONFIGURED` flag + defensive `isinstance(h, logging.StreamHandler)` check; attaches `StreamHandler(sys.stderr)` with formatter `"%(asctime)s %(levelname)s %(name)s: %(message)s"`; sets `propagate = False`. Idempotent across reruns and repeat calls.
- `src/mosaic_dashboard/config.py` — `DEFAULT_DATA_ROOT`, `SESSION_KEY = "data_root_override"`, `CONFIG_TOML_PATH = Path(__file__).resolve().parents[2] / "config.toml"`, and `resolve_data_root() -> Path` implementing D-04.
- `src/mosaic_dashboard/ui/__init__.py` — Package marker for the `ui` subpackage (Plan 05 lands `sidebar.py` here).

## Public API Reference for Plans 03/04/05

For downstream plans, the import surface to consume is:

```python
# Plans 03 + 04 (loaders)
from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns
from mosaic_dashboard.data.errors import SchemaMismatchError  # only if catching

# Plan 05 (app.py + Data Status page + ui/sidebar.py)
from mosaic_dashboard.config import resolve_data_root, SESSION_KEY
from mosaic_dashboard.logging_config import configure as configure_logging
```

Signatures:

```python
class DataLayerError(Exception): ...
class SchemaMismatchError(DataLayerError):
    dataset: str
    missing: set[str]
    present: set[str]  # may be empty set if not provided

def require_columns(
    df: pd.DataFrame,
    required: Iterable[str],
    dataset: str,
) -> None: ...

SESSION_KEY: str = "data_root_override"
DEFAULT_DATA_ROOT: Path  # ~/MOSAIC/MOSAIC-data/processed expanded
CONFIG_TOML_PATH: Path   # repo-root config.toml

def resolve_data_root() -> Path: ...

def configure(level: str = "INFO") -> None: ...  # idempotent
```

## Decisions Made

- **No structural deviation from RESEARCH.md skeletons.** All four modules were implemented essentially as published in `01-RESEARCH.md` §"Data-Access Layer Reference Implementation" and §"Logging & Error Reporting", with minor expansion to docstrings to encode the rationale (D-references) inline.
- **Logging function name kept as `configure`** (not `configure_logging`) per RESEARCH.md skeleton and plan `key_links` `contains: "def configure"`. Callers can alias on import if a more descriptive name is desired in `app.py`.
- **Idempotence guard is double-locked:** the `_CONFIGURED` flag is the fast path; the `isinstance(h, logging.StreamHandler) for h in logger.handlers` check is a defensive backstop for the (rare) case where the module is reimported between calls — handler re-attachment is still suppressed.
- **`CONFIG_TOML_PATH = parents[2] / "config.toml"` was verified against the actual layout:** `src/mosaic_dashboard/config.py` -> `parents[0]=src/mosaic_dashboard/`, `parents[1]=src/`, `parents[2]=repo root`. The verify script confirmed `CONFIG_TOML_PATH.exists()` returns True with Plan 01-01's `config.toml` in place.
- **Empty-string override semantics:** `st.session_state[SESSION_KEY] = ""` is intentionally treated as "no override" (falsy check on the value) so that when the Plan 05 sidebar text input is cleared, resolution falls through to `config.toml` cleanly — verified by the plan's automated test.
- **`resolve_data_root()` not cached:** matches RESEARCH.md §"Resolution function" guidance. Config-toml reads are millisecond-scale and we want edits to the TOML to take effect on next rerun without cache-clearing.

## Idempotence Confirmation

Logging idempotence was explicitly verified by the Task 2 automated check:

1. First `configure()` call: 1 `StreamHandler` attached to `logging.getLogger("mosaic_dashboard")`.
2. Second `configure(level='INFO')` call: handler count unchanged.
3. Third `configure(level='DEBUG')` call (different level): handler count still unchanged; `_CONFIGURED` guard prevents level re-application too — by design.

Test output: `TASK2 OK` (handler count remained at 1 across all three calls).

## Deviations from Plan

None — plan executed exactly as written. All three tasks completed in order; each verify script printed its `TASK{N} OK` marker; the cross-cutting `from mosaic_dashboard.data import errors, _schema; from mosaic_dashboard import logging_config, config` import smoke check passed; no circular-import issues; `_CONFIGURED` idempotence held.

No Rule 1/2/3 auto-fixes triggered. No Rule 4 architectural decisions required.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required for this plan.

## Next Phase Readiness

- **Plan 01-03 (per-subdir loaders, Wave 3):** Can now import `resolve_data_root`, `require_columns`, and the typed exception, and use `logging.getLogger(__name__)` for the "subdir missing" warning path (D-10). All primitives ready.
- **Plan 01-04 (shapefile loader, Wave 3):** Same surface — additionally relies on `resolve_data_root()` for the shapefile-dir glob.
- **Plan 01-05 (UI shell, Wave 4):** Can import `SESSION_KEY` for the sidebar `text_input` `key=` parameter, call `configure()` near the top of `app.py`, and use `resolve_data_root()` to drive the Data Status page's directory enumeration.
- **No blockers or concerns.** The foundation contract published by this plan is the same as what RESEARCH.md anchored, so any later plan that already aligned with the research can land without surprise.

## Self-Check: PASSED

Verified before returning:

- `src/mosaic_dashboard/data/__init__.py` — FOUND
- `src/mosaic_dashboard/data/errors.py` — FOUND
- `src/mosaic_dashboard/data/_schema.py` — FOUND
- `src/mosaic_dashboard/logging_config.py` — FOUND
- `src/mosaic_dashboard/config.py` — FOUND
- `src/mosaic_dashboard/ui/__init__.py` — FOUND
- Commit `c13da32` (Task 1) — FOUND
- Commit `9ff40ce` (Task 2) — FOUND
- Commit `363c663` (Task 3) — FOUND
- `uv run python -c "from mosaic_dashboard.data import errors, _schema; from mosaic_dashboard import logging_config, config"` — exit 0
- `uv run python -c "import mosaic_dashboard.data; import mosaic_dashboard.config; import mosaic_dashboard.logging_config"` — exit 0 (no circular import)

---
*Phase: 01-foundation-data-layer*
*Plan: 02*
*Completed: 2026-05-13*
