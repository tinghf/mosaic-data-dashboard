# Phase 1: Foundation & Data Layer - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up a runnable Streamlit app and a configurable, offline, fresh-read data-access layer over `MOSAIC-data/processed/`. Every later phase (country picker, map, per-subdir views, overlays, drilldown, perf, usability) reads through this layer.

In scope (REQ-mapped):
- DATA-01 — Configurable path to `MOSAIC-data/processed/`
- DATA-02 — Fresh-read on every load (invisible caching allowed)
- DATA-03 — Zero external network calls in the hot path; offline-capable
- DATA-04 — Tolerate upstream additions/renames/missing subdirs (caveat: see D-12 — strict on schema mismatch *within* an expected dataset; lenient on subdir presence)
- ENV-01 — `uv` + pinned deps + committed `uv.lock`
- ENV-02 — Documented one-liner launches the dashboard

Explicitly **not** in this phase:
- Country picker / map / per-subdir views — Phases 2+
- Overlays, drilldown, performance tuning — Phases 4, 6
- Layer captions / usability polish — Phase 7

</domain>

<decisions>
## Implementation Decisions

### Configuration & data-root resolution
- **D-01:** Project ships a committed `config.toml` at repo root with sensible defaults. Teammates can edit in place.
- **D-02:** If no value is set, the data layer falls back to `~/MOSAIC/MOSAIC-data/processed/` (matches the user's local checkout and the documented convention).
- **D-03:** The sidebar exposes an *ephemeral* text-input override for the data-root path. It applies for the current Streamlit session only — it does NOT persist to `config.toml`.
- **D-04:** Resolution order: sidebar override (session) → `config.toml` → default (`~/MOSAIC/MOSAIC-data/processed/`).

### Data-access layer API shape
- **D-05:** **One module per `processed/` subdir** (`mosaic_dashboard.data.who`, `mosaic_dashboard.data.wash`, `mosaic_dashboard.data.enso`, etc.) with **named loader functions** per dataset granularity (e.g., `who.load_annual(country)`, `who.load_weekly(country)`, `enso.load_daily()`, `enso.load_weekly()`, `enso.load_monthly()`).
- **D-06:** Every loader returns a **pandas DataFrame with normalized columns**. Loaders own the rename/reshape from upstream CSV shape to the project's canonical column names. Views never reshape; they just read.
- **D-07:** Country identifier across the whole project is **ISO3** (e.g., `AGO`, `BEN`, `COD`). Matches the existing shapefile filename convention (`AGO_ADM0`, `BEN_ADM0`...). Each loader is responsible for translating to its source's native country key internally if needed.
- **D-08:** When a country is absent from a given dataset, the loader returns an **empty DataFrame** (with the canonical columns). Views check `df.empty` and render their empty-state. No exceptions on the happy path.
- **D-09:** No `Dataset`/metadata wrapper class in Phase 1. Layer captions in Phase 7 will read constants or a small `meta` helper — kept out of Phase 1 to avoid premature abstraction.

### Missing / renamed subdir handling
- **D-10:** If a `processed/` subdir is entirely missing on disk, the loader returns an **empty DataFrame and logs a warning** (single handling pattern with D-08).
- **D-11:** Phase 1 ships a **dedicated "Data Status" Streamlit page** as its primary view. It enumerates each expected subdir under `processed/`, reports presence/absence, file count, and most-recent mtime. This is the first thing a teammate sees and answers "is my data hooked up correctly?" in one screen.
- **D-12:** **Strict on schema mismatch *within* an expected dataset** — if a known CSV is present but a required column is missing or renamed, the loader raises a typed exception (e.g., `SchemaMismatchError`) with the dataset name and missing column. Rationale: tolerating renames silently produces wrong charts; failing loud forces a deliberate code update when upstream changes the contract.
- **D-13:** DATA-04's "tolerates upstream changes without code changes where reasonable" is interpreted as: tolerate **subdir absence and irrelevant file additions** silently (warning only); fail loud on **schema mismatch in an expected dataset**.

### Project layout & entry point
- **D-14:** **`src/` layout with an importable package**: `src/mosaic_dashboard/`. Contains `data/` (per-subdir loader modules), `config.py` (TOML + sidebar override resolution), `app.py` (entry), `pages/` (Streamlit-discovered view files).
- **D-15:** **Streamlit native `pages/` directory** for multi-page navigation. Phase 1 adds one file: `pages/00_Data_Status.py` (zero-prefix to keep it first in the sidebar list). Subsequent phases drop in their own `pages/NN_*.py` files.
- **D-16:** **`pyproject.toml`** with PEP 621 metadata, managed by `uv` (`uv init --package` style). Pinned deps under `[project] dependencies`, committed `uv.lock`. The package is installable.
- **D-17:** Launch one-liner: `uv sync && uv run streamlit run src/mosaic_dashboard/app.py` (or whichever entry path the planner finalizes; documented in README).

### Caching & read-path strategy
- **D-18:** **Streamlit `@st.cache_data` per loader function, keyed on file path + mtime.** Re-reads only when the underlying file's mtime changes. Satisfies DATA-02 (fresh on edit) and front-loads the PERF-01 work.
- **D-19:** **Plain pandas CSV reads** — no parquet sidecars, no polars/duckdb backend in Phase 1. The cache layer is invisible and lives in Streamlit's cache, NOT under `MOSAIC-data/` (preserves the read-only constraint).
- **D-20:** If PERF-01 (sub-second country switch) is not met after Phase 6 measurement, the *internal* cache representation can change without breaking the loader API contract (DataFrame in / out is stable). This decision is reversible.

### Claude's Discretion
- Exact module/file names within the `data/` subpackage beyond the per-subdir-module rule (e.g., whether `who.py` exposes `load_annual` and `load_weekly` or splits to `who_annual.py` / `who_weekly.py`) — Claude picks the cleanest grouping during planning.
- Logging library choice (`logging` stdlib vs `structlog`) — Claude picks; stdlib is the default unless there's a reason to upgrade.
- Specific `SchemaMismatchError` / `DataLayerWarning` exception/event class hierarchy — Claude picks the minimal shape consistent with D-12.
- Whether the Data Status page uses `st.dataframe`, `st.metric`, or a custom layout — implementation detail, planner can choose.
- Default values that ship in `config.toml` (beyond the data path) — Claude picks reasonable defaults; user can override.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level docs
- `.planning/PROJECT.md` — Core value, constraints (offline, read-only, uv lockfile), key decisions log
- `.planning/REQUIREMENTS.md` — Full text of DATA-01..04, ENV-01, ENV-02, and the v2/Out-of-Scope context
- `.planning/ROADMAP.md` §"Phase 1: Foundation & Data Layer" — Goal + 4 success criteria

### Upstream data layout (read-only — do not modify)
- `~/MOSAIC/MOSAIC-data/processed/` — Root of the data the dashboard reads
- `~/MOSAIC/MOSAIC-data/processed/WHO/{annual,daily,weekly}/` — Cholera cases
- `~/MOSAIC/MOSAIC-data/processed/WASH/WASH_data_Sikder_2023.csv` — WASH indicators
- `~/MOSAIC/MOSAIC-data/processed/ENSO/compiled_ENSO_1970_2025_{daily,weekly,monthly}.csv` — ENSO indices
- `~/MOSAIC/MOSAIC-data/processed/demographics/{UN_world_population_prospects_1967_2100.csv, demographics_africa_2000_2023.csv}`
- `~/MOSAIC/MOSAIC-data/processed/OAG/` — Flight mobility (daily/weekly/monthly 2017 means)
- `~/MOSAIC/MOSAIC-data/processed/shapefiles/` — `AFRICA_ADM0.{shp,shx,dbf,prj}` plus per-country `XXX_ADM0.*` (ISO3-prefixed, ~55 countries). **No ADM1/ADM2 shapefiles currently shipped** — relevant for Phase 6 DRILL, noted here so the data layer doesn't assume their existence.
- `~/MOSAIC/MOSAIC-data/processed/{immunity,vaccine_effectiveness,symptomatic,similarity_matrix}/` — Smaller/static layers (Phase 5)

No external specs or ADRs at this time — all decisions captured here and in PROJECT.md/REQUIREMENTS.md.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **None** — this is a greenfield project. Repo contains only `.planning/` and `.git/` at the start of Phase 1.

### Established Patterns
- **None yet** — Phase 1 IS the pattern-setter. Subsequent phases will follow the conventions established here:
  - Per-subdir loader modules under `mosaic_dashboard.data`
  - Normalized DataFrame columns with `country_iso3` as the join key where relevant
  - `@st.cache_data` mtime-keyed for any function reading from disk
  - One Streamlit page file per major view under `src/mosaic_dashboard/pages/`

### Integration Points
- The data layer's public surface (per-subdir loader modules returning normalized DataFrames keyed by ISO3) is the integration point Phases 2–7 build on. Treat it as a stable contract; widen it via additive loader functions in later phases, not by changing existing signatures.

</code_context>

<specifics>
## Specific Ideas

- "Data Status" first-screen view (D-11) is the user's own surface for "did I hook up the dataset correctly?" — model it explicitly as a triage page, not just diagnostics. Include subdir name, exists? (yes/no), file count, latest mtime.
- ISO3 convention (D-07) is anchored on the upstream shapefile filenames already observed (`AGO_ADM0`, `BEN_ADM0`, ...). The MAP phase will lean on this directly, so the data layer must be ISO3-clean from day one.
- The sidebar data-path override (D-03) is for *teammates with multiple checkouts*, not for non-default config — explicit ephemeral semantics (not persisted) are part of the decision.

</specifics>

<deferred>
## Deferred Ideas

- **Parquet / polars / duckdb backend** — explicitly out of Phase 1 (D-19). Revisit in Phase 6 if PERF-01 measurement shows pandas+CSV reads can't hit sub-second country switching with all SSA loaded. Loader API contract is stable across this change (D-20).
- **Per-dataset metadata object** (units, time range, source) — deferred to Phase 7 captions work. Will be added without changing existing loader signatures (additive surface).
- **Persisting the sidebar data-path override to `config.toml`** — out of Phase 1. The override is intentionally ephemeral. If a "save as default" affordance turns out to be wanted, it's a UX phase concern.
- **User-config-file at `~/.config/mosaic-dashboard/config.toml`** — considered (Area 1 Q3 option B/C); not adopted for v1. Repo-root `config.toml` is sufficient for the local-laptop, single-user scope. Reconsider if dashboard moves toward multi-environment usage.
- **ADM1/ADM2 shapefile sourcing** — Phase 6 (DRILL) will face this. Upstream `processed/shapefiles/` currently ships ADM0 only. Not Phase 1's problem, but flagged here so the planner doesn't accidentally bake assumptions about subnational geometry availability into the foundational data layer.

</deferred>

---

*Phase: 01-Foundation & Data Layer*
*Context gathered: 2026-05-13*
