# Phase 1: Foundation & Data Layer - Research

**Researched:** 2026-05-13
**Domain:** Streamlit + uv + pandas data-layer scaffolding (Python 3.13, WSL2 Linux)
**Confidence:** HIGH (all critical patterns verified against current official docs; versions checked against PyPI today)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01** Project ships a committed `config.toml` at repo root with sensible defaults. Teammates can edit in place.
- **D-02** If no value is set, the data layer falls back to `~/MOSAIC/MOSAIC-data/processed/`.
- **D-03** Sidebar exposes an *ephemeral* text-input override for the data-root path (session only, not persisted to TOML).
- **D-04** Resolution order: sidebar override (session) → `config.toml` → default (`~/MOSAIC/MOSAIC-data/processed/`).
- **D-05** One module per `processed/` subdir under `mosaic_dashboard.data.*` with named loader functions per dataset granularity.
- **D-06** Every loader returns a pandas DataFrame with normalized columns. Loaders own the rename/reshape.
- **D-07** Country identifier is **ISO3** (`AGO`, `BEN`, `COD`); matches the existing shapefile filename convention.
- **D-08** Country absent from a dataset → loader returns an **empty DataFrame** (with canonical columns). No exceptions on the happy path.
- **D-09** No `Dataset`/metadata wrapper class in Phase 1.
- **D-10** Missing subdir → empty DataFrame + log warning (single handling pattern with D-08).
- **D-11** Phase 1 ships a dedicated **"Data Status" Streamlit page** as its primary view (subdir presence/absence, file count, mtime).
- **D-12** Strict on schema mismatch *within* an expected dataset — raise typed exception (e.g., `SchemaMismatchError`) with dataset name and missing column.
- **D-13** DATA-04 interpretation: tolerate subdir absence and irrelevant file additions silently (warning only); fail loud on schema mismatch in an expected dataset.
- **D-14** `src/` layout with importable package: `src/mosaic_dashboard/`. Contains `data/`, `config.py`, `app.py`, `pages/`.
- **D-15** Streamlit native `pages/` directory for multi-page navigation. Phase 1 ships `pages/00_Data_Status.py`.
- **D-16** `pyproject.toml` with PEP 621 metadata, managed by `uv` (`uv init --package` style). Pinned deps under `[project] dependencies`, committed `uv.lock`. Package is installable.
- **D-17** Launch one-liner: `uv sync && uv run streamlit run src/mosaic_dashboard/app.py`.
- **D-18** `@st.cache_data` per loader function, keyed on file path + mtime.
- **D-19** Plain pandas CSV reads in Phase 1. No parquet/polars/duckdb backend.
- **D-20** If PERF-01 fails later, internal cache representation can change without breaking loader API contract.

### Claude's Discretion
- Module/file names within `data/` subpackage beyond per-subdir-module rule (e.g., `who.py` exposing `load_annual` and `load_weekly` vs splitting to `who_annual.py` / `who_weekly.py`).
- Logging library choice (`logging` stdlib vs `structlog`) — stdlib default unless reason to upgrade.
- Specific `SchemaMismatchError` / `DataLayerWarning` exception/event class hierarchy.
- Whether Data Status page uses `st.dataframe`, `st.metric`, or custom layout.
- Default values that ship in `config.toml` beyond the data path.

### Deferred Ideas (OUT OF SCOPE)
- Parquet / polars / duckdb backend (revisit in Phase 6 if PERF-01 fails).
- Per-dataset metadata object (Phase 7 captions).
- Persisting sidebar data-path override to `config.toml`.
- User-config-file at `~/.config/mosaic-dashboard/config.toml`.
- ADM1/ADM2 shapefile sourcing (Phase 6).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | Configurable path to `MOSAIC-data/processed/` | §5 (config resolution + sidebar override sketch); D-01..D-04 |
| DATA-02 | Fresh-read on every load (invisible caching allowed) | §4 (mtime-keyed `@st.cache_data` pattern); D-18 |
| DATA-03 | Zero external network calls in the hot path; offline-capable | §2 (no network-fetching deps); pandas/streamlit are local reads |
| DATA-04 | Tolerate upstream additions/renames/missing subdirs | §4 (subdir-missing → empty DF + warning); §6 (`SchemaMismatchError` for strict-mismatch case); D-10/D-12/D-13 |
| ENV-01 | `uv` + pinned deps + committed `uv.lock` | §2 (`uv init --package` workflow, `uv sync` commits lockfile) |
| ENV-02 | Documented one-liner launches the dashboard | §2 (`uv sync && uv run streamlit run src/mosaic_dashboard/app.py`) |
</phase_requirements>

## TL;DR

Five-bullet recap of how Phase 1 gets built:

1. **Scaffold with `uv init --package mosaic-dashboard`** (gives src/ layout, installable package, `uv_build` backend, [project.scripts] hook). Then declare `streamlit`, `pandas`, `tomli` (or use Python 3.11+ `tomllib`) as runtime deps. `uv sync` produces `uv.lock` automatically.
2. **Entry point lives at `src/mosaic_dashboard/app.py`**; Streamlit `pages/` directory sits beside it at `src/mosaic_dashboard/pages/`. Pages auto-discover; filename `00_Data_Status.py` → sidebar label "Data Status", sorted first (numeric prefixes sort as numbers, not strings).
3. **`@st.cache_data` with mtime in the function signature** is the canonical mtime-keyed cache pattern. Each loader is `def load(path: Path, mtime: float, country: str) -> DataFrame`; the caller does `mtime = path.stat().st_mtime` first. Underscore-prefixed args are NOT hashed — useful for non-hashable params like file handles, but for our case we just pass primitives.
4. **Manual column-set validation beats pandera for this scope.** A single `_require_columns(df, required: set, dataset: str)` helper that raises a `SchemaMismatchError(dataset, missing)` is ~20 lines, has zero new deps, and gives identical error clarity. Reach for pandera only if validation rules grow beyond column presence (which they won't in Phase 1).
5. **Sidebar override + `pages/` collision is real.** The "widget defined in entrypoint persists across pages" idiom works ONLY with `st.navigation` — explicitly NOT with the `pages/` directory (locked by D-15). Therefore Phase 1 needs a **shared `sidebar()` helper called at the top of every page** (incl. `app.py`), reading/writing `st.session_state["data_root_override"]` directly. The widget is rendered per page; its value lives in session_state so it survives navigation. This sets the pattern Phase 2's country picker will reuse.

**Primary recommendation:** Use `uv init --package` from the repo root, scaffold the `mosaic_dashboard.data` subpackage with one module per `processed/` subdir, build a single `_require_columns` helper + `SchemaMismatchError` for strict schema enforcement, write a shared `sidebar.render()` function called from `app.py` and `pages/00_Data_Status.py`, and use the `@st.cache_data` + explicit-mtime-argument pattern for every loader. No third-party validation, plotting, or logging libraries needed in Phase 1.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Filesystem reads of `processed/*.csv` | Data layer (`mosaic_dashboard.data.*`) | — | Locked by D-05/D-06; views never touch disk. |
| Path resolution (config + sidebar override) | Config (`mosaic_dashboard.config`) | Session state | Pure resolution function; sidebar pushes override into `st.session_state`; resolver reads from there. |
| Sidebar UI rendering | UI helper (`mosaic_dashboard.ui.sidebar`) | Session state | Helper called from each page (since pages/ idiom can't host stateful entrypoint widgets — see §3). |
| Data Status page | View (`pages/00_Data_Status.py`) | Data layer (read-only metadata helpers) | Page enumerates expected subdirs, calls `Path.exists`/`stat`, presents a table. |
| Caching | Streamlit runtime (`@st.cache_data`) | — | Invisible per D-02; lives in Streamlit's in-memory cache, NOT under `MOSAIC-data/`. |
| Schema validation | Data layer (`mosaic_dashboard.data._schema`) | Exception hierarchy (`mosaic_dashboard.data.errors`) | One `_require_columns` helper + one exception class. No upstream library. |
| Logging | stdlib `logging` | Streamlit terminal (stderr) | `logging.warning()` for "subdir missing"; `st.warning()` reserved for user-facing UI on the Data Status page. |

## Project Constraints (from CLAUDE.md)

No CLAUDE.md exists in the repo root at research time. The planner should consider creating one in Phase 1 to lock in:
- Read-only access to `~/MOSAIC/MOSAIC-data/` (never write under that path; D-19).
- ISO3 as the canonical country identifier (D-07).
- `uv` is the only package manager (no pip/conda mixing).
- Streamlit `pages/` directory convention; no ad-hoc page-routing libs.

This is a recommendation, not a constraint. Planner can also defer CLAUDE.md to Phase 7 (usability polish surfaces conventions naturally).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | **1.57.0** | Web app framework + `@st.cache_data` + `pages/` navigation | Locked (PROJECT.md). Latest stable as of 2026-05-13 per PyPI. `[VERIFIED: pypi.org/pypi/streamlit/json fetched 2026-05-13]` |
| pandas | **3.0.3** | CSV reads, DataFrame, normalized-column contract | Locked by D-06. Latest stable on PyPI today. `[VERIFIED: pypi.org/pypi/pandas/json fetched 2026-05-13]` |
| Python | **3.11+** (recommend pin to 3.12 or 3.13) | Runtime | Need ≥3.11 for stdlib `tomllib`. Local environment is 3.13.12. `[VERIFIED: python3 --version]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `tomllib` | 3.11+ stdlib | Read `config.toml` (binary mode) | First choice — zero deps. |
| stdlib `logging` | stdlib | Warnings when subdir missing (D-10) | Default per Claude's Discretion in CONTEXT.md. |
| stdlib `pathlib.Path` | stdlib | All filesystem ops, mtime via `.stat().st_mtime` | Used throughout data layer. |

### Tooling

| Tool | Version | Purpose | Status |
|------|---------|---------|--------|
| uv | **0.11.14** (PyPI latest); installed: **0.8.2** | Package manager, lockfile, project init | `[VERIFIED: pypi.org/pypi/uv/json fetched 2026-05-13]`. Installed version (0.8.2) works for our needs but planner may want to add a step to `uv self update` for parity with `uv_build>=0.11.14,<0.12` requirement. |
| uv_build | `>=0.11.14,<0.12` | Build backend for `uv init --package` | Auto-configured by `uv init --package`. `[CITED: docs.astral.sh/uv/concepts/projects/init/]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `uv_build` backend | `hatchling` | Hatchling is more portable (works without uv) and is the broader Python community standard. `uv_build` is the default from `uv init --package` and integrates tightly with uv. **Recommendation: stick with `uv_build`** since uv is locked in (ENV-01); no migration cost saved by switching. |
| Manual column-set validation | `pandera` (~3MB + numpy compat surface) | Pandera shines for type/range/check validation. For pure "required columns present" enforcement (D-12), a 20-line helper is clearer and adds zero deps. **Recommendation: manual.** Re-evaluate if Phase 5/6 needs dtype or value-range validation. |
| stdlib `logging` | `structlog`, `loguru` | Structured logging is overkill for a local single-user dashboard. **Recommendation: stdlib `logging`.** |
| `pages/` directory (D-15 locked) | `st.navigation` + `st.Page` (Streamlit ≥1.36) | `st.navigation` is the *currently recommended* multipage API and would make D-03 (persistent sidebar) trivial. But D-15 locks `pages/` — research respects that. **Workaround in §5.** |
| `tomli` 3rd-party | stdlib `tomllib` (Python 3.11+) | Identical API. `tomllib` is stdlib for Python ≥3.11; no reason to add a dep. |

**Verified install command** (planner expands inside `uv init --package` flow):
```bash
uv add streamlit pandas
# stdlib only: tomllib, logging, pathlib (no separate install)
```

`[VERIFIED: streamlit 1.57.0, pandas 3.0.3, uv 0.11.14 — all pulled from PyPI JSON metadata 2026-05-13]`

## Project Scaffolding

### Exact scaffolding command sequence (from zero)

```bash
# 1. From the repo root (which currently has only .planning/ and .git/):
uv init --package --name mosaic-dashboard --python 3.13
# Creates:
#   .python-version
#   README.md (or leaves existing — verify)
#   pyproject.toml         (PEP 621, with [build-system] = uv_build)
#   src/mosaic_dashboard/__init__.py
# `uv init --package` is mandatory for D-14 (src/ layout) + D-16 (installable package).
# `uv init` (default, no flag) does NOT create src/ layout and does NOT install as a package.

# 2. Pin Python version (uv writes .python-version automatically; verify it says 3.13).

# 3. Add runtime deps:
uv add streamlit pandas
#   → updates [project.dependencies] and writes uv.lock

# 4. Create the package internals (no command — just files; planner's tasks):
#   src/mosaic_dashboard/app.py                       (Streamlit entry)
#   src/mosaic_dashboard/config.py                    (TOML + sidebar resolution)
#   src/mosaic_dashboard/data/__init__.py
#   src/mosaic_dashboard/data/errors.py               (SchemaMismatchError)
#   src/mosaic_dashboard/data/_schema.py              (_require_columns helper)
#   src/mosaic_dashboard/data/who.py
#   src/mosaic_dashboard/data/wash.py
#   src/mosaic_dashboard/data/enso.py
#   src/mosaic_dashboard/data/demographics.py
#   src/mosaic_dashboard/data/oag.py
#   src/mosaic_dashboard/data/shapefiles.py
#   src/mosaic_dashboard/data/immunity.py
#   src/mosaic_dashboard/data/vaccine_effectiveness.py
#   src/mosaic_dashboard/data/symptomatic.py
#   src/mosaic_dashboard/data/similarity_matrix.py
#   src/mosaic_dashboard/ui/__init__.py
#   src/mosaic_dashboard/ui/sidebar.py                (shared sidebar render fn)
#   src/mosaic_dashboard/pages/00_Data_Status.py      (Streamlit auto-discovers)
#   config.toml                                       (repo root, NOT under .streamlit/)

# 5. Sync (writes uv.lock; installs project + deps into .venv):
uv sync

# 6. Launch:
uv run streamlit run src/mosaic_dashboard/app.py
```

### Resulting `pyproject.toml` shape (after `uv init --package` + `uv add`)

```toml
[project]
name = "mosaic-dashboard"
version = "0.1.0"
description = "Local Streamlit dashboard for the MOSAIC processed-data inspector"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.57,<2.0",
    "pandas>=3.0,<4.0",
]

[project.scripts]
# Optional: gives `uv run mosaic-dashboard` if planner wants a CLI shim later.
# Phase 1 launches via `streamlit run`, so this can be omitted or stubbed.

[build-system]
requires = ["uv_build>=0.11.14,<0.12"]
build-backend = "uv_build"
```

`[CITED: docs.astral.sh/uv/concepts/projects/init/ — exact shape from `uv init --package` output]`

**Version pins note:** The `streamlit>=1.57,<2.0` and `pandas>=3.0,<4.0` ranges balance reproducibility (`uv.lock` pins exact versions) with allowing patch updates. `uv.lock` is the contract teammates rely on (ENV-01); the `pyproject.toml` ranges are just floors/ceilings.

### Where the entry point lives

**Decision: `src/mosaic_dashboard/app.py`** (locked by D-17).

- Streamlit's `pages/` discovery finds `pages/` *relative to the entry script's directory* — so `src/mosaic_dashboard/pages/` must sit next to `app.py`. `[CITED: docs.streamlit.io/develop/concepts/multipage-apps/pages-directory]`
- `uv sync` installs `mosaic_dashboard` as an editable package in the venv, so any `from mosaic_dashboard.data import who` import inside `app.py` or any page resolves correctly. `[VERIFIED: uv_run editable install behavior, github.com/astral-sh/uv issues/13454]`
- The streamlit-template community repo (`data-sloth/uv-streamlit-setup`) keeps the entry script at the repo root (`hello.py`) — this is a *different* pattern and we are NOT using it because D-14/D-17 lock the entry to inside the package. The trade-off: with the entry inside the package, Streamlit's `pages/` auto-discovery looks inside `src/mosaic_dashboard/pages/`, which is exactly what we want (the package is self-contained).

### `config.toml` (repo root)

```toml
# config.toml — Mosaic Dashboard configuration (committed to git)
# Teammates can edit this file in place. The sidebar override (per-session) takes precedence.

[data]
# Absolute path to MOSAIC-data/processed/. Defaults to ~/MOSAIC/MOSAIC-data/processed/ if empty
# or absent (matches the documented teammate convention).
root = "~/MOSAIC/MOSAIC-data/processed/"

[logging]
# Stdlib logging level for the dashboard's own loggers (DEBUG/INFO/WARNING/ERROR).
level = "INFO"
```

**No collision with Streamlit's own config:** Streamlit reads its runtime settings from `.streamlit/config.toml`, NOT from a repo-root `config.toml`. Our repo-root `config.toml` is a separate, project-owned file. `[VERIFIED: docs.streamlit.io/develop/api-reference/configuration/config.toml — "Streamlit stores configuration in a `.streamlit/config.toml` file in your working directory"]`

If Phase 1 ever needs Streamlit-specific overrides (e.g., dark theme, server port), those go in `.streamlit/config.toml`, separate from our project config.

## Streamlit Multi-Page Conventions

### `pages/` directory discovery rules (locked by D-15)

- **Only `.py` files inside `pages/` are pages.** Files in subdirectories of `pages/` are ignored. `[CITED: docs.streamlit.io/develop/concepts/multipage-apps/pages-directory]`
- **Filename grammar:** `number_separator_identifier.py` (all three parts optional; separator can be `_`, space, or `-`).
- **Ordering:** Files with a leading number sort before files without one. Number is compared as int (so `03_X.py` and `3_X.py` sort identically). Files without a number sort alphabetically by label after the numbered ones. `[CITED: same URL]`
- **Label transformation rules:**
  - Underscores in the identifier portion are rendered as spaces in the sidebar label.
  - Leading and trailing underscores in the identifier are dropped.
  - Sequential underscores collapse to a single space.
  - The numeric prefix and separator are NOT shown in the label.
  - `[CITED: discuss.streamlit.io / docs — "Any underscores within the page's identifier are treated as spaces. Therefore, leading and trailing underscores are not shown."]`
- **URL paths:** Consecutive `_` and ` ` collapse to one `_`. `00_Data_Status.py` → `/Data_Status`. `[CITED: same source]`
- **Examples:**
  - `pages/00_Data_Status.py` → sidebar label: **"Data Status"**, URL `/Data_Status`, sort order 0.
  - `pages/01_Country_Picker.py` (future Phase 2) → label "Country Picker", URL `/Country_Picker`, sort order 1.

### Entry-point file = homepage

`app.py` IS the homepage. When the user visits the root URL, they see `app.py`'s render. The sidebar auto-shows links to `app.py` (typically labeled by `st.set_page_config(page_title=...)` or filename) and every file under `pages/`.

### `st.set_page_config` interaction

Call `st.set_page_config(...)` at the top of `app.py` (as the very first Streamlit call). Per-page overrides can be set at the top of each `pages/NN_*.py` file. Settings like `page_title`, `page_icon`, `layout="wide"`, and `initial_sidebar_state="expanded"` are page-scoped when called inside a page; the entry-script call is the default. `[CITED: docs.streamlit.io/develop/api-reference/configuration/st.set_page_config]`

**Recommended Phase 1 entrypoint settings:**
```python
st.set_page_config(
    page_title="Mosaic Data Dashboard",
    page_icon="🗺",            # Optional; emoji omitted in actual file if "no emojis" policy
    layout="wide",
    initial_sidebar_state="expanded",
)
```

### Gotchas the planner must know

1. **`pages/` directory pattern does NOT support the "entrypoint widget persists across pages" idiom** — that's `st.navigation`-only. `[CITED: docs.streamlit.io/develop/concepts/multipage-apps/widgets — "This method does not work if you define your app with the pages/ directory."]` See §5 for the workaround.
2. **Widget keys reset on page switch by default.** If the same key is defined on page A and page B, Streamlit treats them as separate widgets unless their value is mirrored through `st.session_state` with a non-widget-key. Underscore-prefix trick (or just rendering the widget through a shared helper that always reads/writes the same session_state key) solves this.
3. **Widgets not rendered on a given run are cleaned up at the end of that run.** If the sidebar isn't rendered on a page, its session-state-bound key may be cleared. Solution: render the sidebar on EVERY page via the shared helper. `[CITED: discuss.streamlit.io thread on widget state — "When Streamlit gets to the end of an app run, it will delete the data for any widgets that were not rendered."]`
4. **Page files run as scripts, not modules.** Each `pages/NN_*.py` is executed by Streamlit as a top-level script. They can still `from mosaic_dashboard.config import ...` because the package is installed editably (step 5 in scaffolding). Do NOT use relative imports inside `pages/` — `from ..data import who` will fail.

## Data-Access Layer Reference Implementation

This section provides concrete code excerpts the planner can paste into task `action` fields.

### Exception class (`src/mosaic_dashboard/data/errors.py`)

```python
"""Typed exceptions for the data layer."""

from __future__ import annotations


class DataLayerError(Exception):
    """Base class for all data-layer errors."""


class SchemaMismatchError(DataLayerError):
    """Raised when an expected dataset is present but its schema does not match contract.

    Per D-12: strict on schema mismatch within an expected dataset. We tolerate missing
    subdirs and unknown extra files silently, but a known CSV missing a required column
    is loud and explicit.
    """

    def __init__(self, dataset: str, missing: set[str], present: set[str] | None = None):
        self.dataset = dataset
        self.missing = set(missing)
        self.present = set(present) if present else set()
        missing_str = ", ".join(sorted(self.missing))
        msg = f"Schema mismatch in dataset '{dataset}': missing required columns {{{missing_str}}}"
        super().__init__(msg)
```

### Schema check helper (`src/mosaic_dashboard/data/_schema.py`)

```python
"""Lightweight schema enforcement: required column-set check.

Phase 1 scope (D-12): verify required columns are present. Dtype, value-range, and
nullability checks are deferred to later phases if needed. This deliberately avoids
pulling in pandera for one type of check.
"""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from .errors import SchemaMismatchError


def require_columns(df: pd.DataFrame, required: Iterable[str], dataset: str) -> None:
    """Raise SchemaMismatchError if any column in `required` is missing from `df`.

    Args:
        df: The DataFrame to check (typically just-read from CSV).
        required: Column names that MUST be present.
        dataset: Human-readable dataset name used in the error message (e.g., "WHO/weekly").

    Returns:
        None. Raises on failure. Extra columns beyond `required` are tolerated.
    """
    required_set = set(required)
    missing = required_set - set(df.columns)
    if missing:
        raise SchemaMismatchError(dataset=dataset, missing=missing, present=set(df.columns))
```

### Caching pattern (`@st.cache_data` mtime-keyed)

The canonical idiom in current Streamlit is to **pass mtime as a hashable function argument**. Streamlit hashes args to compute the cache key — when mtime changes, the key changes, and the cache misses (and re-reads the file). `[CITED: docs.streamlit.io/develop/concepts/architecture/caching and st.cache_data API reference]`

```python
"""WHO loader — illustrative pattern; other subdirs follow identically."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

WHO_REQUIRED_COLUMNS_ANNUAL = {"country_iso3", "year", "cases"}
WHO_REQUIRED_COLUMNS_WEEKLY = {"country_iso3", "year", "week", "cases"}


def load_annual(country: str | None = None) -> pd.DataFrame:
    """Load WHO annual cholera cases. Filter to `country` (ISO3) if given.

    Returns an empty DataFrame with canonical columns if:
      - the WHO/ subdir is absent (logs a warning), OR
      - the WHO/annual/ subdir is absent, OR
      - `country` is not present in the data (D-08: no exception, empty DF).

    Raises:
      SchemaMismatchError: if the file exists but is missing required columns.
    """
    root = resolve_data_root()
    annual_dir = root / "WHO" / "annual"
    if not annual_dir.exists():
        import logging
        logging.getLogger("mosaic_dashboard.data.who").warning(
            "WHO/annual directory not found at %s — returning empty DataFrame", annual_dir,
        )
        return _empty_annual()

    # Single-file convention; if upstream changes to multiple files, this needs revisiting.
    files = sorted(annual_dir.glob("*.csv"))
    if not files:
        return _empty_annual()

    # Use the most recent file's mtime as part of the cache key.
    csv_path = files[0]
    mtime = csv_path.stat().st_mtime
    df = _read_who_annual_cached(str(csv_path), mtime)

    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_annual()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_who_annual_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached CSV read keyed on (path, mtime). Re-reads only when mtime changes.

    `mtime` is in the signature solely to participate in the cache key — Streamlit
    hashes all non-underscore args to build the key.
    """
    df = pd.read_csv(path)
    require_columns(df, WHO_REQUIRED_COLUMNS_ANNUAL, dataset="WHO/annual")
    # Normalize column names here (D-06) — example, adjust to actual upstream column names:
    # df = df.rename(columns={"iso3": "country_iso3", "year_num": "year"})
    return df


def _empty_annual() -> pd.DataFrame:
    """Canonical empty DataFrame for the WHO/annual contract."""
    return pd.DataFrame({c: pd.Series(dtype="object") for c in WHO_REQUIRED_COLUMNS_ANNUAL})
```

**Pattern rules captured here:**
1. **Public function (`load_annual`)** is NOT cached itself — it handles path resolution, filtering, and empty-state. Only the disk-read portion is cached.
2. **Cached function (`_read_who_annual_cached`)** takes `path: str` (not `Path` — Streamlit's hasher handles strings cleanly) and `mtime: float`. Both are simple hashable types.
3. **Schema check happens INSIDE the cached function**, so a malformed CSV cached once doesn't keep silently failing on subsequent calls — the error is raised on the first miss and propagated up.
4. **Filtering by country happens OUTSIDE the cache** so we cache the full DataFrame once and slice per country (cheap pandas op).
5. **Empty-state is owned by `load_annual`**, returning a DataFrame with canonical columns and zero rows (D-08). Views see uniform shape regardless of whether data exists.

`[CITED: docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data — leading-underscore exclusion, cache-key hashing of non-underscore args; discuss.streamlit.io/t/refresh-cache-when-panda-data-file-changes/4841 — older but identical pattern for mtime-in-signature]`

### Per-subdir loader module map (Claude's discretion area)

Recommended grouping (one module per `processed/` subdir, multiple functions per module when granularities differ):

| Module | Functions | Rationale |
|--------|-----------|-----------|
| `data/who.py` | `load_annual(country)`, `load_weekly(country)`, `load_daily(country)` | Three time granularities of the same source share rename/reshape logic; one module avoids cross-imports. |
| `data/wash.py` | `load(country)` | Single CSV — one function. |
| `data/enso.py` | `load_daily()`, `load_weekly()`, `load_monthly()` | No country filter (global indices). |
| `data/demographics.py` | `load_un_wpp(country)`, `load_africa_2000_2023(country)` | Two distinct sources; functions named after the underlying file's identity. |
| `data/oag.py` | `load_daily(country)`, `load_weekly(country)`, `load_monthly(country)` | Mobility — country filter has "involving country" semantics; planner should clarify in implementation. |
| `data/shapefiles.py` | `load_africa()`, `load_country(country)` | Returns GeoDataFrame-or-DataFrame in Phase 1; geopandas not required for "list/check existence" only. |
| `data/immunity.py` | `load(country)` | Static layer. |
| `data/vaccine_effectiveness.py` | `load(country)` | Static layer. |
| `data/symptomatic.py` | `load(country)` | Static layer. |
| `data/similarity_matrix.py` | `load()` | Returns full matrix; views slice. |

**Note on shapefiles in Phase 1:** D-11 (Data Status page) only needs to know subdir presence + file count + mtime. Phase 1 does NOT need to *parse* the shapefiles — just stat them. Defer geopandas dependency to Phase 2 (which is when the SSA map renders). Phase 1 `data/shapefiles.py` can expose a simple `available_countries() -> list[str]` that parses ISO3 prefixes from filenames in `processed/shapefiles/`.

## Configuration + Sidebar Override

### Resolution function (`src/mosaic_dashboard/config.py`)

```python
"""Configuration resolution: sidebar → config.toml → default (D-04)."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import streamlit as st

DEFAULT_DATA_ROOT = Path("~/MOSAIC/MOSAIC-data/processed").expanduser()
CONFIG_TOML_PATH = Path(__file__).resolve().parents[2] / "config.toml"  # repo root
SESSION_KEY = "data_root_override"  # set by the sidebar widget


def resolve_data_root() -> Path:
    """Resolution order per D-04: sidebar (session_state) → config.toml → default.

    Returns the resolved path. Does NOT check that it exists — that's a separate
    concern surfaced on the Data Status page.
    """
    # 1. Sidebar override (ephemeral, session-scoped, D-03)
    override = st.session_state.get(SESSION_KEY)
    if override:
        return Path(override).expanduser()

    # 2. Repo-root config.toml (D-01)
    if CONFIG_TOML_PATH.exists():
        with CONFIG_TOML_PATH.open("rb") as f:
            cfg = tomllib.load(f)
        configured = cfg.get("data", {}).get("root", "").strip()
        if configured:
            return Path(configured).expanduser()

    # 3. Default (D-02)
    return DEFAULT_DATA_ROOT
```

**Notes:**
- `tomllib` is stdlib in Python 3.11+ — opens in *binary* mode (`"rb"`). `[CITED: docs.python.org/3/library/tomllib.html]`
- `expanduser()` handles `~/MOSAIC/...` for any user account, including the WSL2 case (`/home/tinghf/...`).
- `parents[2]` walks `src/mosaic_dashboard/config.py` → `src/mosaic_dashboard/` → `src/` → repo-root. Verify the depth matches actual layout when planning tasks.
- Function is NOT cached. The TOML read is cheap (~milliseconds), and we want changes to `config.toml` to take effect on the next rerun without manual cache-clearing.

### Sidebar render helper (`src/mosaic_dashboard/ui/sidebar.py`)

```python
"""Shared sidebar UI. Called from app.py and every pages/*.py to keep state alive
across page navigation (works around pages/-directory limitation: see RESEARCH.md §3)."""

from __future__ import annotations

import streamlit as st

from mosaic_dashboard.config import SESSION_KEY


def render() -> None:
    """Render the shared sidebar. Must be called once per page (incl. entrypoint).

    The data-root override is bound to st.session_state[SESSION_KEY] via the
    widget's `key` parameter. Streamlit reads the existing session_state value on
    each render, so the widget's displayed value survives page navigation as long
    as this function is called on every page.
    """
    st.sidebar.header("Mosaic Dashboard")

    # Initialize session_state slot if absent. We never write a default value here,
    # because an empty string means "fall back to config.toml" (per D-04).
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = ""

    st.sidebar.text_input(
        "Data root override (session only)",
        key=SESSION_KEY,
        placeholder="Leave blank to use config.toml or default (~/MOSAIC/MOSAIC-data/processed)",
        help=(
            "Ephemeral override of the data root for this browser session. "
            "Does NOT persist to config.toml. Resolution order: this field → "
            "config.toml → default."
        ),
    )
```

### Why a shared helper instead of an "entrypoint widget"

The Streamlit-recommended pattern of "define the sidebar widget once in your entrypoint, it persists everywhere" works ONLY with `st.navigation` + `st.Page`. With the `pages/` directory (locked by D-15), each page is its own top-level script and the entrypoint is NOT re-executed when the user clicks a sidebar page link.

The two working patterns for `pages/`-style apps are:

1. **Shared helper called per page** (recommended here, simplest): every page's first lines are `from mosaic_dashboard.ui.sidebar import render; render()`. The widget's value lives in `st.session_state[SESSION_KEY]` and persists because `session_state` survives page navigation.
2. **Underscore-prefix temp-key trick** (more complex; needed only if the widget itself has expensive default-computation logic): widget uses key `_data_root_override`, an `on_change` callback copies to `data_root_override`. Not needed for a plain text input.

`[CITED: discuss.streamlit.io/t/sharing-the-same-widget-across-several-pages-of-a-multi-page-app-using-session-state/54440; docs.streamlit.io/develop/concepts/multipage-apps/widgets — "If you define an identical widget on two different pages, then the widget will reset to its default value when you switch pages."]`

**Why this generalizes for Phase 2:** Phase 2's country picker will follow the same pattern — `ui/sidebar.py` grows a `country_picker()` widget, the picker's value lives in `st.session_state["selected_country"]`, every page calls `sidebar.render()` at its top. No refactor needed in Phase 2.

### `app.py` skeleton

```python
"""Mosaic Data Dashboard — entrypoint. Phase 1 lands the user on a brief
welcome screen and exposes the Data Status page via the auto-discovered sidebar."""

from __future__ import annotations

import streamlit as st

from mosaic_dashboard.ui.sidebar import render as render_sidebar

st.set_page_config(
    page_title="Mosaic Data Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

st.title("Mosaic Data Dashboard")
st.write(
    "Inspect the MOSAIC-data/processed/ datasets layer by layer. "
    "Start with **Data Status** in the sidebar to verify your local checkout."
)
```

## Logging & Error Reporting

### Logger setup pattern

Phase 1 uses stdlib `logging` (Claude's discretion in CONTEXT.md, with stdlib as the default). The key concern is that Streamlit re-runs each script on every interaction — naive `logging.basicConfig()` at module top-level adds duplicate handlers on every rerun. The fix is to gate handler attachment.

```python
"""src/mosaic_dashboard/logging_config.py"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure(level: str = "INFO") -> None:
    """Configure stdlib logging for the dashboard. Idempotent across Streamlit reruns.

    Call once from app.py near the top. Logs surface in the terminal (stderr) where
    `streamlit run` is executing — NOT in the browser. Use st.warning() / st.error()
    for browser-visible messages.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger("mosaic_dashboard")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    # Don't double-add if handler already exists (defensive).
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
    root.propagate = False

    _CONFIGURED = True
```

Modules then use named child loggers:
```python
log = logging.getLogger(__name__)  # "mosaic_dashboard.data.who"
log.warning("WHO/annual directory not found at %s", annual_dir)
```

### `logging.warning()` vs `st.warning()` — clear separation

| Surface | API | When to use |
|---------|-----|-------------|
| **Terminal (stderr)** | `logging.warning(...)` | Operator/teammate debugging surface. Used per D-10 when a subdir is missing. Also captured by any teammate who runs `streamlit run` in a terminal. |
| **Browser UI** | `st.warning(...)`, `st.error(...)`, `st.info(...)` | User-visible state. Used on the Data Status page (D-11) to render a colored banner next to a missing subdir's row. |

For D-10's "missing subdir → empty DF + warning" requirement, the planner should emit BOTH:
1. `logging.warning(...)` from the loader (for terminal-level diagnostics).
2. A row on the Data Status page (D-11) with a clear "missing" indicator (Status column = "MISSING").

The data layer itself never calls `st.warning()` — that would couple the loader to Streamlit's runtime. The Data Status page is the only place that translates layer state into UI.

### Streamlit's own logger

Streamlit child loggers are set with `propagate=False` and have their own `StreamHandler` — so they don't interfere with ours as long as we use the `mosaic_dashboard` logger namespace. `[CITED: discuss.streamlit.io/t/streamlit-logging-with-python-logger/51951 + github.com/streamlit/streamlit/blob/develop/lib/streamlit/logger.py]`

The `streamlit --log-level` CLI flag controls Streamlit's *own* logs, not our app's. To set our app's level, read it from `config.toml` `[logging] level` and pass to `configure(level=...)` in `app.py`.

### Exception hierarchy (final)

```
DataLayerError(Exception)
└── SchemaMismatchError(DataLayerError)   # raised by require_columns()
```

That's it for Phase 1. If Phase 5+ adds dtype validation, a sibling `DataTypeMismatchError(DataLayerError)` would slot in cleanly. Keeping the hierarchy minimal honors D-09 ("no premature abstraction").

## Validation Architecture

> `nyquist_validation: false` in `.planning/config.json` — formal test framework section is skipped. What follows is the acceptance-criteria checklist Phase 1 must pass before `/gsd-verify-work` calls the phase done. These translate directly into the planner's `must_haves` / verification tasks.

### Acceptance checks (manual + scripted)

| # | Acceptance Criterion | How to verify | Maps to |
|---|----------------------|---------------|---------|
| A1 | `uv sync` succeeds from a fresh clone with no manual data step | `git clone ... && cd ... && uv sync` exits 0; `.venv/` and `uv.lock` exist | ENV-01, ROADMAP §1 criterion 1 |
| A2 | `uv run streamlit run src/mosaic_dashboard/app.py` launches the dashboard | Streamlit prints "You can now view your Streamlit app in your browser." and serves on default port 8501 | ENV-02, ROADMAP §1 criterion 1 |
| A3 | Data Status page is reachable and renders | Navigate to `/Data_Status` (or click "Data Status" in sidebar); page renders a table of expected subdirs with presence/file-count/mtime columns | D-11 |
| A4 | With network disconnected, the dashboard still loads | `ip link set <iface> down` (or disconnect WSL2 network) → reload localhost:8501 → app still renders Data Status page | DATA-03, ROADMAP §1 criterion 3 |
| A5 | Intentionally-missing subdir produces empty DF + warning (no crash) | Temporarily rename `~/MOSAIC/MOSAIC-data/processed/WHO/` to `WHO.bak/` → reload → Data Status shows WHO row as "MISSING"; `logging.warning` line appears in terminal; no traceback in UI | DATA-04, D-10, ROADMAP §1 criterion 4 |
| A6 | Intentionally-malformed CSV produces `SchemaMismatchError` | Temporarily edit a copy of a WHO CSV to remove a required column → invoke `who.load_annual()` (e.g., from a small `pages/01_Sandbox.py` test page OR from `uv run python -c "..."`) → `SchemaMismatchError` raised with dataset name + missing-column set | D-12, D-13 |
| A7 | Sidebar override changes the effective path mid-session | In sidebar, type an alternate valid path → Data Status table updates to reflect that path's contents on next interaction | DATA-01, D-03, D-04 |
| A8 | Edit to a CSV under `processed/` shows on next page interaction without restart | Edit one of the WHO CSVs (add a value); reload Data Status → mtime column shows the new value; underlying loader returns the new value when next called | DATA-02, D-18 |
| A9 | `uv.lock` is committed | `git ls-files | grep uv.lock` returns a hit | ENV-01 |
| A10 | README documents the launch one-liner | README contains `uv sync && uv run streamlit run src/mosaic_dashboard/app.py` (or the exact path that ships) | ENV-02, ROADMAP §1 criterion 1 |

**A5/A6 implementation hint for the planner:** Set up a tiny `pages/99_Sandbox.py` for ad-hoc verification, OR rely on manual runs of `uv run python -c "from mosaic_dashboard.data import who; print(who.load_annual())"`. No formal pytest suite is required by config (`nyquist_validation: false`), but the planner may still choose to scaffold a `tests/` directory with one smoke test per acceptance check — it's good hygiene and zero added dependency cost (pytest can be added under `[dependency-groups.dev]` in pyproject.toml).

## Pitfalls

Stack-specific things that bite people in this exact configuration:

### P1: `pages/` filename numeric-prefix off-by-one
**What goes wrong:** Developer writes `pages/0_Data_Status.py` expecting "ordered first" — works. Then adds `pages/10_Compare.py` and `pages/2_Country.py`. They expect alphabetic sort (`10` before `2`), but Streamlit sorts numerically (`2` before `10`).
**How to avoid:** Use two-digit zero-padded prefixes consistently (`00_`, `01_`, `02_`...). Phase 1 ships `00_Data_Status.py` — keep that convention for Phase 2+.

### P2: `src/` layout + `streamlit run` import error
**What goes wrong:** Page does `from mosaic_dashboard.data import who`, Streamlit raises `ModuleNotFoundError`. Cause: `uv sync` was skipped, so the package is not installed in `.venv` and `src/` is not on `sys.path`.
**How to avoid:** Always launch via `uv run streamlit run ...` (not bare `streamlit run`). `uv run` ensures the project is installed in the venv before exec. The launch one-liner in D-17 already does this; don't deviate. If a teammate reports `ModuleNotFoundError`, first ask whether they ran `uv sync`. `[CITED: github.com/astral-sh/uv issue 13454 — sys.path behavior with editable install in src layout]`

### P3: `@st.cache_data` returns mutable DataFrame; in-place edits leak across calls
**What goes wrong:** A loader returns `df`, a view does `df["country"] = df["country"].str.upper()` in-place, next call to loader returns the mutated df.
**Reality check:** Streamlit's docs explicitly say `@st.cache_data` returns a **copy** of the cached value within each user session — so in-place mutation of the returned object does NOT corrupt the cached value. However, mutating the cached object from inside the cached function before returning DOES corrupt the cache. `[CITED: docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data — "Within each user session, an @st.cache_data-decorated function returns a copy of the cached return value"]`
**How to avoid:** Never mutate `df` inside the cached function after the schema check. Always return a fresh DataFrame from `pd.read_csv()` (which is already fresh).

### P4: `config.toml` mistaken for `.streamlit/config.toml`
**What goes wrong:** Teammate sets a Streamlit-runtime option (e.g., `theme.primaryColor`) in repo-root `config.toml`. Streamlit ignores it because it only reads `.streamlit/config.toml`.
**How to avoid:** Document loudly in repo-root `config.toml` header comments: "This file configures the **Mosaic Dashboard application**, not Streamlit itself. For Streamlit runtime settings, use `.streamlit/config.toml`." The two filenames are unfortunately similar.

### P5: WSL2 `~/MOSAIC/` path resolution under uv
**What goes wrong:** WSL2 user has `~/MOSAIC/MOSAIC-data/` on the Linux filesystem (`/home/tinghf/MOSAIC/...`) but a teammate on a different machine has it under `/mnt/c/...` (Windows mount) or `~/code/MOSAIC/...`. The hardcoded `~/MOSAIC/...` default fails.
**How to avoid:** The whole point of `config.toml` (D-01) + sidebar override (D-03) is to cover this. The default is just the most-common case; teammates with different layouts edit `config.toml`. Document this in the README.

### P6: pandas `read_csv` silently parses dates wrong
**What goes wrong:** `pd.read_csv()` does not parse date columns by default. A column named `date` arrives as `object` dtype. Views then do `df.sort_values("date")` and get lexicographic order, not chronological.
**How to avoid:** Each loader explicitly declares date columns: `pd.read_csv(path, parse_dates=["date"])`. This is loader-internal normalization (D-06: loaders own reshape).

### P7: `st.cache_data` and `pathlib.Path` hashing
**What goes wrong:** Passing `Path` directly into a `@st.cache_data` function — Streamlit's hasher historically had inconsistent behavior with Path objects.
**How to avoid:** Pass `str(path)` into cached functions, keep `Path` objects in the outer (non-cached) public function. The skeleton in §4 already does this.

### P8: Cache survives the schema-mismatch error inappropriately
**What goes wrong:** First call to `_read_who_annual_cached("path", 12345.0)` raises `SchemaMismatchError`. The exception is NOT cached (Streamlit only caches successful returns), so the next call retries. This is correct behavior, but teammates sometimes assume cache is poisoned and waste time debugging.
**How to avoid:** Document in the code comment that `SchemaMismatchError` from a cached function is re-raised on each call until the underlying file changes mtime (i.e., until the schema is fixed and the file is re-saved). `[VERIFIED: docs.streamlit.io/develop/concepts/architecture/caching — only successful returns are cached]`

### P9: Session-state slot used before initialization
**What goes wrong:** A page reads `st.session_state[SESSION_KEY]` before the sidebar has rendered (e.g., the page does `if st.session_state[SESSION_KEY]: ...` at the top, before calling `render_sidebar()`). KeyError.
**How to avoid:** ALWAYS call `render_sidebar()` as the first non-`set_page_config` action on every page. The `render()` function ensures the key exists.

### P10: `uv init --package` overwriting an existing README
**What goes wrong:** Repo currently has `.planning/` only — no README at root. `uv init --package` may create one. If a teammate runs it again, behavior depends on `--no-readme` / interactive prompts.
**How to avoid:** Run `uv init --package` exactly once during scaffolding; do not include it in a re-runnable setup script. Commit the resulting files. Subsequent teammates run `uv sync` only.

## Runtime State Inventory

Phase 1 is greenfield (creates new code; does not rename or migrate anything). The Runtime State Inventory categories all evaluate as "None — verified: this phase creates files rather than transforming existing state."

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no existing databases or stored state in the repo. `~/MOSAIC/MOSAIC-data/` is upstream and read-only per PROJECT.md constraint. | None. |
| Live service config | None — no running services tied to this project yet. | None. |
| OS-registered state | None — no Task Scheduler/launchd/systemd registrations. | None. |
| Secrets/env vars | None — DATA-03 mandates offline-only; no external API keys or auth. | None. |
| Build artifacts | None — no `egg-info/`, `dist/`, `build/`, or compiled artifacts exist yet. `uv sync` will create `.venv/` (gitignored) on first run. | Verify `.venv/` is in `.gitignore`. |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | All scaffolding + launch | YES | 0.8.2 (installed) vs 0.11.14 (PyPI latest) | None needed; planner may add a `uv self update` step but 0.8.2 supports all required commands. |
| Python | uv-managed runtime | YES | 3.13.12 | None — covers `requires-python = ">=3.11"`. |
| `~/MOSAIC/MOSAIC-data/processed/` | Data layer at runtime | YES | — | The sidebar override + `config.toml` handle alternative locations per D-01/D-03. |
| Network | Out of scope | N/A | — | DATA-03 explicitly says no network in hot path; `uv sync` is the only network-touching step, runs once. |
| `streamlit`, `pandas` packages | App runtime | NO (not yet installed) | — | `uv add streamlit pandas` installs them; PyPI access required for the one-time install. |

**Missing dependencies with no fallback:** None. PyPI access is required for the initial `uv sync` but this is one-time setup, not hot-path.

**Missing dependencies with fallback:** None.

`[VERIFIED: command -v uv → /home/tinghf/.local/bin/uv; uv --version → uv 0.8.2; python3 --version → Python 3.13.12; ls ~/MOSAIC/MOSAIC-data/processed/ → 10 subdirs confirmed]`

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Upstream WHO CSVs have a `country_iso3` column (or use the ISO3 prefix in filenames). Phase 1 normalizes to `country_iso3` per D-07. | §4 (loader skeleton column-set example) | LOW — if the actual upstream column is `iso3` or `country_code`, the loader's `rename(...)` line handles it. Planner should add a "discover actual upstream column names" task to Wave 0 of the plan. |
| A2 | Required-column sets in the example loader (`{"country_iso3", "year", "cases"}`, etc.) are correct for WHO/annual. | §4 | MEDIUM — actual column names should be discovered by reading one CSV during planning. The pattern (set-difference check) is correct regardless; only the literal set values may change. |
| A3 | The `pages/` directory at `src/mosaic_dashboard/pages/` is discovered when launching from `src/mosaic_dashboard/app.py`. | §2, §3 | LOW — Streamlit docs confirm `pages/` is relative to the entry script's directory. A quick "is the page in the sidebar?" check after scaffolding catches any path mismatch. |
| A4 | `uv_build` is the right build backend choice over `hatchling` for this project. | §2 | LOW — both work. `uv_build` is the default from `uv init --package`; switching to `hatchling` later is a 5-line change in `pyproject.toml`. |
| A5 | The `SESSION_KEY = "data_root_override"` slot name doesn't collide with anything Streamlit reserves. | §5 | LOW — Streamlit reserves keys prefixed with `_streamlit_`; user keys are otherwise unrestricted. |
| A6 | Schema-mismatch behavior of `@st.cache_data` (exceptions are NOT cached, retried on next call) is stable in Streamlit 1.57. | §8 (P8) | LOW — verified against current docs; this has been Streamlit's behavior across multiple recent releases. |
| A7 | Streamlit 1.57.0 + pandas 3.0.3 are mutually compatible. | §2 | LOW — both are current stable releases. `uv sync` will surface any conflict immediately. Planner can add a "verify import" smoke test in scaffolding. |

## Open Questions / Decisions Deferred to Planner

These are items the research could not lock without either reading actual upstream data files or running a small code experiment. The planner can resolve them during Wave 0:

1. **Exact upstream column names per subdir.**
   - **What we know:** D-07 mandates `country_iso3` as the canonical join column; D-06 says loaders own renames. The data layout (subdirs, file names) is confirmed.
   - **What's unclear:** The actual column names in each upstream CSV (e.g., does WHO ship `iso3`, `iso_code`, `country_id`?).
   - **Recommendation:** Planner adds one Wave 0 task: "Read one row from each `processed/` subdir's CSV; record the exact upstream column names per dataset in a scratch doc; use that to populate the `rename(columns={...})` line in each loader." This is ~30 minutes of work and de-risks every loader implementation.

2. **OAG "involving country" semantics.**
   - **What we know:** OAG is flight-mobility data with daily/weekly/monthly granularity.
   - **What's unclear:** Does mobility involving country X include flights *to* X, *from* X, or both? The loader's `load_*(country)` filter shape depends on this.
   - **Recommendation:** Defer to Phase 3 (OAG view). Phase 1's `oag.py` returns the full DataFrame for a country (both directions if both are present), letting the view in Phase 3 decide presentation.

3. **Shapefile reading library in Phase 1.**
   - **What we know:** D-11 (Data Status page) needs to enumerate shapefile presence. D-15 mentions `pages/00_Data_Status.py`. Phase 2 will render the SSA map.
   - **What's unclear:** Whether Phase 1 should already pull in `geopandas` (heavy: pulls in `fiona`, `shapely`, `pyproj` — ~50MB) just to count files, or use stdlib `Path.glob`.
   - **Recommendation:** Use `Path.glob("*_ADM0.shp")` in Phase 1. Defer geopandas to Phase 2. The `shapefiles.py` loader exposes only `available_countries()` + presence/mtime metadata in Phase 1; full geometry reads come in Phase 2.

4. **Whether to scaffold a `tests/` directory in Phase 1.**
   - **What we know:** `nyquist_validation: false` in `.planning/config.json` — formal test framework is not required.
   - **What's unclear:** Whether the planner wants light pytest smoke tests (e.g., "load each subdir's loader, assert returned shape is DataFrame") for confidence.
   - **Recommendation:** Planner's call. If yes, add `pytest>=8.0` under `[dependency-groups.dev]` in pyproject.toml (uv supports dependency groups natively) and one `tests/smoke_test.py`. If no, rely on the manual A1–A10 acceptance checks in §7.

5. **CLAUDE.md authoring in Phase 1 vs later.**
   - **What we know:** No CLAUDE.md exists. Project conventions (ISO3, uv-only, pages/ pattern) will be set in Phase 1.
   - **What's unclear:** Whether to author CLAUDE.md now (helps subsequent agents) or wait until Phase 7 polish.
   - **Recommendation:** Author a minimal CLAUDE.md in Phase 1 with: (a) the launch one-liner, (b) "data is read-only at `~/MOSAIC/MOSAIC-data/`", (c) "ISO3 is the canonical country id", (d) "always `uv run` — never bare python or streamlit". Roughly 30 lines, pays dividends immediately.

## Sources

### Primary (HIGH confidence)

- **Streamlit official docs (current 2026):**
  - `docs.streamlit.io/develop/concepts/multipage-apps/pages-directory` — pages/ discovery, numeric prefix ordering, filename → label rules
  - `docs.streamlit.io/develop/concepts/multipage-apps/widgets` — entrypoint-widget pattern, page switching widget reset rules, the explicit statement "This method does not work if you define your app with the pages/ directory"
  - `docs.streamlit.io/develop/concepts/architecture/caching` — `@st.cache_data` semantics, leading-underscore exclusion, copy-on-return for DataFrames
  - `docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data` — full API, persist, ttl, max_entries, show_spinner, `.clear()` method
  - `docs.streamlit.io/develop/api-reference/configuration/config.toml` — `.streamlit/config.toml` is Streamlit's own config (not our app's)

- **uv official docs:**
  - `docs.astral.sh/uv/concepts/projects/init/` — `uv init` vs `--package` vs `--lib` vs `--app`; exact resulting pyproject.toml shape; src/ layout creation; uv_build backend pin
  - `docs.astral.sh/uv/guides/projects/` — `uv sync` installs project editably

- **PyPI metadata fetched 2026-05-13:**
  - streamlit 1.57.0
  - pandas 3.0.3
  - uv 0.11.14

- **Local environment probes (2026-05-13):**
  - `uv --version` → 0.8.2 (installed)
  - `python3 --version` → 3.13.12 (miniforge3)
  - `ls ~/MOSAIC/MOSAIC-data/processed/` → confirms 10 subdirs including WHO/{annual,daily,weekly}, shapefiles, ENSO, OAG, etc.

### Secondary (MEDIUM confidence)

- `discuss.streamlit.io/t/streamlit-logging-with-python-logger/51951` — community-validated pattern for stdlib logging in Streamlit reruns (`@st.cache_resource` for handler-attach idempotence, or a one-shot guard like our `_CONFIGURED` flag).
- `discuss.streamlit.io/t/sharing-the-same-widget-across-several-pages-of-a-multi-page-app-using-session-state/54440` — the shared-helper pattern for `pages/`-style apps; flicker warning is real but minor.
- `github.com/data-sloth/uv-streamlit-setup` — template repo demonstrating uv + Streamlit + src layout; uses a different (root-level) entry-point convention than ours but confirms the editable-install workflow.
- `github.com/astral-sh/uv/issues/13454` — sys.path behavior with editable install in src layout under uv.
- `packaging.python.org` — src layout vs flat layout rationale and pyproject.toml standard.

### Tertiary (LOW confidence — flagged for validation if relied on)

- None in this research that the plan should hinge on. The "manual schema check vs pandera" recommendation is judgment, not citation; planner should accept or reject explicitly.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against PyPI; uv init flags verified against current official docs.
- Architecture patterns (pages/, cache_data, sidebar): HIGH — every behavioral claim cross-referenced with current Streamlit docs.
- Schema validation library choice: HIGH — manual approach is provably sufficient for D-12's narrow contract; pandera trade-off documented in alternatives table.
- Logging pattern: MEDIUM — stdlib pattern is well-established; the idempotence guard pattern is community-derived but verified to work via the official Streamlit logger source code referenced.
- Acceptance checks (§7): HIGH — every check maps to an explicit decision or requirement, and each is performable manually in <2 minutes.
- Pitfalls (§8): HIGH for documented ones; one (P3) is a "the docs explicitly contradict the common fear" finding worth highlighting.

**Research date:** 2026-05-13
**Valid until:** 2026-06-13 (30 days — Streamlit and pandas both ship minor updates monthly; revalidate version numbers if planning slips past this date).
