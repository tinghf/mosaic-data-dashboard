# Project Conventions

Locked conventions for any agent (human or AI) working in this repo. These are
hard constraints — violating them breaks downstream plans and/or the
read-only contract on the upstream data.

## 1. Launch via `uv run` — never bare `streamlit` or `python`

The canonical launch one-liner is:

```bash
uv sync && uv run streamlit run src/mosaic_dashboard/app.py
```

`uv run` ensures the project is installed editably into `.venv/` before
execution, which puts `src/mosaic_dashboard/` on `sys.path`. Running bare
`streamlit run` or `python -m streamlit ...` will raise `ModuleNotFoundError`
on any `from mosaic_dashboard.xxx import yyy`. If a teammate hits an import
error, first ask whether they ran `uv sync` and used `uv run`.

## 2. `~/MOSAIC/MOSAIC-data/` is READ-ONLY

The dashboard reads CSVs and shapefiles from a local clone of MOSAIC-data.
**Never write under that path** — no caching sidecars, no normalization
outputs, no auto-generated index files. All caching lives in Streamlit's
in-memory `@st.cache_data` store. If a loader needs to persist anything, it
goes under the repo or a system temp dir, not under the data root.

## 3. ISO3 is the canonical country identifier

The whole project keys on three-letter ISO3 country codes (e.g., `AGO`, `BEN`,
`COD`). This matches the shapefile filename convention shipped upstream
(`AGO_ADM0.shp`, `BEN_ADM0.shp`, ...). Loaders own the rename from each
dataset's native country column to `country_iso3`. Views and the country picker
never see anything other than ISO3.

## 4. `uv` is the only package manager; pages live under `pages/`

- Use `uv add <pkg>` to add dependencies. Never `pip install`, never `conda`.
  Mixing managers corrupts the lockfile.
- Multi-page navigation uses Streamlit's native `src/mosaic_dashboard/pages/`
  directory. No third-party page-routing libraries (e.g., `streamlit-pages`,
  `hydralit`). Page filenames are two-digit zero-padded for stable ordering
  (`00_Data_Status.py`, `01_Country_Picker.py`, ...).
