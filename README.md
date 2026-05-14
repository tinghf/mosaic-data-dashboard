# Mosaic Data Dashboard

A local Streamlit dashboard for the MOSAIC team to explore the processed datasets
backing the MOSAIC project — an agent-based metapopulation simulation of cholera
transmission across Sub-Saharan Africa. The dashboard reads directly from a local
clone of [MOSAIC-data](https://github.com/InstituteforDiseaseModeling/MOSAIC-data)
and lets a modeler pick a country and see every relevant data layer (WHO cholera
cases, ENSO, WASH, demographics, OAG flight mobility, immunity, vaccine
effectiveness, symptomatic fraction, similarity matrix) side by side, with
time-series overlays that surface relationships between environmental/structural
drivers and outbreak outcomes.

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) and Python >=3.11. Clone the repo, then:

```bash
uv sync && uv run streamlit run src/mosaic_dashboard/app.py
```

The first command installs the project into a local `.venv/` and pins the
dependency graph via `uv.lock`. The second launches Streamlit on
http://localhost:8501. No external network calls happen in the hot path — once
`uv sync` has finished, the dashboard is fully offline.

## Configuring the data path

The dashboard reads CSV/shapefile inputs from a local checkout of
`MOSAIC-data/processed/`. It resolves the data root in this order (first match
wins):

1. **Sidebar override** — Each Streamlit session exposes a text input in the
   sidebar where you can paste an alternate path. This applies for the current
   browser session only and is NOT persisted to disk.
2. **`config.toml` at the repo root** — Set `[data] root = "..."` here for a
   per-checkout default. Committed to git, so a teammate cloning the repo
   inherits whatever you check in.
3. **Default** — `~/MOSAIC/MOSAIC-data/processed/` if neither of the above is
   set. Matches the documented teammate convention.

**WSL2 / non-standard layouts:** If your `MOSAIC-data/` lives somewhere other
than `~/MOSAIC/MOSAIC-data/`, edit the `root` value in `config.toml`. Both
absolute paths and `~`-prefixed paths are accepted; `~` is expanded against the
current user's home directory.

The dashboard never writes under the data root — it is read-only.

## Project layout

```
mosaic-dashboard/
├── config.toml                          # Application config (data path, log level)
├── pyproject.toml                       # PEP 621 metadata + dependencies (uv-managed)
├── uv.lock                              # Pinned dependency graph (committed)
├── README.md                            # This file
├── CLAUDE.md                            # Project conventions for AI agents
└── src/
    └── mosaic_dashboard/                # Installable Python package
        ├── __init__.py
        ├── app.py                       # Streamlit entry point (created in Plan 05)
        ├── config.py                    # Data-root resolution (Plan 02)
        ├── data/                        # Per-subdir loader modules (Plans 03-04)
        ├── ui/                          # Shared UI helpers (sidebar, ...)
        └── pages/                       # Streamlit-discovered view files
```

Phase 1 (this milestone) builds the foundation: package scaffold, config layer,
data-access layer, and a Data Status page. Subsequent phases add the country
picker, SSA map, per-layer views, overlays, and subnational drilldown.
