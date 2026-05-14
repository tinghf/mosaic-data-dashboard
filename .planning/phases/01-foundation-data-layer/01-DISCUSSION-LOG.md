# Phase 1: Foundation & Data Layer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-13
**Phase:** 01-Foundation & Data Layer
**Areas discussed:** Data-root config mechanism, Data-access layer API shape, Missing/renamed subdir handling, Project layout & entry point, Caching & read-path (perf-shaped, batched)

---

## Data-root config mechanism

### Q1 — How should the path to `MOSAIC-data/processed/` be configured?

| Option | Description | Selected |
|--------|-------------|----------|
| Env var only (`MOSAIC_DATA_PATH`) | Simplest. Set once in shell or .env. No UI knob. | |
| Config file (TOML in repo or `~/.config`) | Committed defaults + local overrides. More discoverable. | ✓ |
| Env var + Streamlit sidebar override | Env var as default, sidebar text input lets user point at a different path mid-session without restarting. | |
| Streamlit sidebar only (entered every session) | Most discoverable, least convenient for repeat use. | |

**User's choice:** Config file (TOML)

### Q2 — Default behavior when no path is configured at all?

| Option | Description | Selected |
|--------|-------------|----------|
| Try `~/MOSAIC/MOSAIC-data/processed/` | Convention-over-config; matches user's local checkout. | ✓ |
| No default — show a friendly setup screen | Most explicit; safer for teammates with different layouts. | |
| Try a list of candidate paths in order | Forgiving but more magic. | |

**User's choice:** Try `~/MOSAIC/MOSAIC-data/processed/`

### Q3 — Where should the config TOML live?

| Option | Description | Selected |
|--------|-------------|----------|
| Committed `config.toml` in repo root | Single file in project root with sensible defaults. | ✓ |
| User config at `~/.config/mosaic-dashboard/config.toml` | Per-user, lives outside the repo. Standard XDG. | |
| Both — user config overrides repo defaults | Most flexible; more code. | |

**User's choice:** Committed `config.toml` in repo root

### Q4 — Can the user override the data path live in the running app?

| Option | Description | Selected |
|--------|-------------|----------|
| No — TOML only, restart to change | Keeps the data layer simple. | |
| Yes — sidebar text input as ephemeral override | TOML is the persistent default; sidebar input points at a different `processed/` dir for this session only. | ✓ |

**User's choice:** Yes — sidebar text input as ephemeral override

**Notes:** Resolution order ends up as: sidebar override (session) → `config.toml` → `~/MOSAIC/MOSAIC-data/processed/` default.

---

## Data-access layer API shape

### Q1 — What shape should the data-access layer expose to view code?

| Option | Description | Selected |
|--------|-------------|----------|
| One module per subdir, named loader fns | e.g., `from mosaic.data.who import load_annual`. Easy to read, parallels `processed/` structure. | ✓ |
| Single registry: `get_dataset('WHO', 'annual', country=...)` | One function dispatches across subdirs. | |
| Lazy DataFrame accessor object | `data.who.annual(country='AGO')` style. Harder to type-check and discover. | |
| Both — typed loaders + a thin registry over them | Most flexible; small overhead. | |

**User's choice:** One module per subdir, named loader fns

### Q2 — What should every loader return?

| Option | Description | Selected |
|--------|-------------|----------|
| pandas DataFrame, normalized columns | Loaders own rename/reshape. Views never reshape. | ✓ |
| Raw DataFrame as the CSV gives it | Less data-layer code; more divergence between views. | |
| DataFrame + a metadata object (units, source, time range) | Self-documenting layers. | |

**User's choice:** pandas DataFrame, normalized columns

### Q3 — Country identifier convention across all loaders?

| Option | Description | Selected |
|--------|-------------|----------|
| ISO3 (AGO, BEN, COD) | Matches shapefile filename convention. Stable, language-neutral. | ✓ |
| Country name | More human-readable but messy across subdirs. | |
| Whatever each subdir uses; map at the loader boundary | Most robust to upstream variation; small mapping table needed. | |

**User's choice:** ISO3

### Q4 — How should loaders handle a country that doesn't exist in this dataset?

| Option | Description | Selected |
|--------|-------------|----------|
| Return empty DataFrame | Predictable. Views check `df.empty`. | ✓ |
| Raise typed exception (`CountryNotFound`) | Explicit handling at view boundary. | |
| Return None | Less type-clean than empty DataFrame downstream. | |

**User's choice:** Return empty DataFrame

**Notes:** Aligns with the empty-DF pattern for missing subdirs — one handling shape across the data layer.

---

## Missing/renamed subdir handling

### Q1 — When a `processed/` subdir is missing entirely, what should the loader return?

| Option | Description | Selected |
|--------|-------------|----------|
| Empty DataFrame + warning logged | One handling pattern with the missing-country case. | ✓ |
| Raise typed exception (`DataLayerMissing`) | Force callers to handle. More boilerplate. | |
| Return None | Pythonic 'absent' signal. Less consistent. | |

**User's choice:** Empty DataFrame + warning logged

### Q2 — Should the dashboard expose a 'data status' check showing which subdirs were found / missing?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — a dedicated 'Data Status' page in Phase 1 | Discovery page listing each subdir, presence, file count, latest mtime. Also satisfies "app loads with no manual data step." | ✓ |
| Yes — inline status in sidebar / footer | Compact; less obtrusive. | |
| No — each view handles its own missing data | No single-source-of-truth for "is dataset OK?" | |

**User's choice:** Dedicated 'Data Status' page in Phase 1

### Q3 — When file shapes change upstream, how strict should loaders be?

| Option | Description | Selected |
|--------|-------------|----------|
| Strict — fail loudly if expected column is missing | Catches upstream drift early; some maintenance overhead. | ✓ |
| Lenient — best-effort rename map + log a warning | Matches DATA-04 "tolerates upstream changes." | |
| Silent — return whatever pandas read | Bad fit for "tolerates without code changes" bar. | |

**User's choice:** Strict — fail loudly

**Notes:** DATA-04's intent is clarified in CONTEXT.md (D-13): tolerate subdir-level changes silently, fail loud on schema mismatch within an expected dataset to prevent silently wrong charts.

---

## Project layout & entry point

### Q1 — How should the codebase be laid out?

| Option | Description | Selected |
|--------|-------------|----------|
| Importable package + Streamlit multi-page (`src/mosaic_dashboard/` + `pages/`) | Scales across 7 phases. | ✓ |
| Single `app.py` with all views inline | Simplest start, unwieldy by Phase 4. | |
| Flat layout: `app.py` + `data.py` + `pages/` | Lighter than full package, less scalable. | |

**User's choice:** Importable package + Streamlit multi-page

### Q2 — Streamlit multi-page navigation: how should views surface?

| Option | Description | Selected |
|--------|-------------|----------|
| Streamlit native `pages/` (auto-discovered) | Sidebar list of views for free. Each phase drops in a file. | ✓ |
| Custom sidebar router | More layout freedom at the cost of writing routing. | |
| Defer — single page in Phase 1 | Multi-page setup in Phase 2 instead. | |

**User's choice:** Streamlit native `pages/`

### Q3 — Python project metadata?

| Option | Description | Selected |
|--------|-------------|----------|
| `pyproject.toml` with PEP 621 (uv default) | Standard, future-proof. | ✓ |
| `pyproject.toml` + editable install | Cleaner imports. | |

**User's choice:** `pyproject.toml` with PEP 621 (uv default)

---

## Caching & read-path strategy (perf-shaped, batched)

### Q1 — Caching strategy for the data layer?

| Option | Description | Selected |
|--------|-------------|----------|
| `@st.cache_data` per loader with mtime keyed | Re-reads only when file mtime changes. Standard Streamlit pattern. | ✓ |
| No caching in Phase 1; add later if PERF demands | Simplest; might be fast enough already. | |
| Manual mtime + pickle/parquet cache layer | More control; more code. | |

**User's choice:** `@st.cache_data` per loader with mtime keyed

### Q2 — Read path / on-disk format strategy?

| Option | Description | Selected |
|--------|-------------|----------|
| Read CSVs directly (pandas) every time | Simplest. Cache handles hot path. | ✓ |
| Read CSV once, write a parquet sidecar invisibly | Risks writing near `MOSAIC-data/` (violates read-only). | |
| Read CSVs with polars or duckdb backend | Adds a dep; pandas at the boundary. | |

**User's choice:** Read CSVs directly (pandas) every time

**Notes:** Parquet/polars/duckdb is explicitly deferred to Phase 6 if PERF-01 isn't met (D-20). Loader API contract is stable across that potential change.

---

## Claude's Discretion

The following are intentionally left to the planner / executor:
- Exact splits of loader modules within `mosaic_dashboard.data` (e.g., `who.py` exposing `load_annual`/`load_weekly` vs `who_annual.py`/`who_weekly.py`).
- Logging library (`logging` stdlib vs `structlog`).
- Shape of the `SchemaMismatchError` exception hierarchy.
- Layout of the Data Status page (`st.dataframe`/`st.metric`/custom).
- Defaults that ship inside `config.toml` beyond the data path.

## Deferred Ideas

Captured for future phases (also reflected in CONTEXT.md `<deferred>`):
- Parquet / polars / duckdb backend — Phase 6 if PERF-01 fails.
- Per-dataset metadata object (units, time range, source) — Phase 7 captions.
- Persisting the sidebar data-path override to `config.toml` — out of Phase 1.
- User-config-file at `~/.config/mosaic-dashboard/config.toml` — not adopted for v1.
- ADM1/ADM2 shapefile sourcing — Phase 6 DRILL concern; flagged so data layer doesn't assume their existence.
