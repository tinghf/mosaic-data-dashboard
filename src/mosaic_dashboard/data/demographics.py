"""Demographics loaders.

Two distinct sources under `MOSAIC-data/processed/demographics/`:

- **UN World Population Prospects** (1967–2100, global, ISO3-keyed).
- **Africa demographics** (2000–2023, Africa-only, daily birth/death rates).

Each gets its own public ``load_*(country)`` function, REQUIRED_COLUMNS set,
and empty-DataFrame factory — the two files have different shapes so they
don't share a schema (per COLUMN_DISCOVERY.md §demographics).

Empty-state contract (D-08, D-10, D-13):
- Missing `demographics/` subdir or missing expected CSV → empty DataFrame +
  `logging.warning(...)`.
- File present, missing required columns → `SchemaMismatchError` (D-12).
- Country absent → empty DataFrame.

Cache contract (D-18, D-20): public/private split; private reader is
`@st.cache_data`-decorated and keyed on (path, mtime).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

#: UN WPP columns (post-rename). Year-resolution; no date column.
DEMOGRAPHICS_REQUIRED_COLUMNS_UN_WPP: set[str] = {
    "country_iso3",
    "year",
    "total_population",
    "births_per_1000",
    "deaths_per_1000",
}

#: Africa 2000-2023 columns (post-rename). Uses ``population`` rather than
#: UN WPP's ``total_population`` and has daily birth/death rates.
DEMOGRAPHICS_REQUIRED_COLUMNS_AFRICA: set[str] = {
    "country_iso3",
    "year",
    "population",
    "births_per_day",
    "deaths_per_day",
}

_UN_WPP_FILENAME = "UN_world_population_prospects_1967_2100.csv"
_AFRICA_FILENAME = "demographics_africa_2000_2023.csv"


# --- UN World Population Prospects -----------------------------------------


def load_un_wpp(country: str | None = None) -> pd.DataFrame:
    """Load UN World Population Prospects, optionally filtered to one ISO3 country.

    Args:
        country: ISO3 country code. When ``None``, returns the full global
            table; when set, returns only rows where
            ``country_iso3 == country`` (empty DataFrame if absent — D-08).

    Returns:
        DataFrame with canonical columns ``{country_iso3, year,
        total_population, births_per_1000, deaths_per_1000}``. Empty
        (canonical columns, zero rows) when the demographics subdir is
        missing, the expected CSV is missing, or the country is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    csv_path = _resolve_demographics_csv(_UN_WPP_FILENAME)
    if csv_path is None:
        return _empty_un_wpp()
    mtime = csv_path.stat().st_mtime
    df = _read_un_wpp_cached(str(csv_path), mtime)
    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_un_wpp()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_un_wpp_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached UN WPP CSV read keyed on (path, mtime)."""
    df = pd.read_csv(path)
    df = df.rename(columns={"iso_code": "country_iso3"})
    require_columns(df, DEMOGRAPHICS_REQUIRED_COLUMNS_UN_WPP, dataset="demographics/UN_WPP")
    return df


def _empty_un_wpp() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in DEMOGRAPHICS_REQUIRED_COLUMNS_UN_WPP}
    )


# --- Africa 2000–2023 ------------------------------------------------------


def load_africa_2000_2023(country: str | None = None) -> pd.DataFrame:
    """Load Africa demographics (2000–2023), optionally filtered to one ISO3 country.

    Args:
        country: ISO3 country code. When ``None``, returns the full African
            table; when set, returns only rows where
            ``country_iso3 == country`` (empty DataFrame if absent — D-08).

    Returns:
        DataFrame with canonical columns ``{country_iso3, year, population,
        births_per_day, deaths_per_day}``. Empty (canonical columns, zero
        rows) when the demographics subdir is missing, the expected CSV is
        missing, or the country is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    csv_path = _resolve_demographics_csv(_AFRICA_FILENAME)
    if csv_path is None:
        return _empty_africa()
    mtime = csv_path.stat().st_mtime
    df = _read_africa_cached(str(csv_path), mtime)
    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_africa()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_africa_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached Africa-demographics CSV read keyed on (path, mtime)."""
    df = pd.read_csv(path)
    df = df.rename(columns={"iso_code": "country_iso3"})
    require_columns(
        df,
        DEMOGRAPHICS_REQUIRED_COLUMNS_AFRICA,
        dataset="demographics/africa_2000_2023",
    )
    return df


def _empty_africa() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in DEMOGRAPHICS_REQUIRED_COLUMNS_AFRICA}
    )


# --- Internal helper -------------------------------------------------------


def _resolve_demographics_csv(filename: str) -> Path | None:
    """Resolve ``<root>/demographics/<filename>``; warn + return None on miss.

    Subdir absence and missing expected file are BOTH warned and treated as
    empty per D-13 interpretation. Only schema-mismatch in a *present* file
    raises.
    """
    root = resolve_data_root()
    subdir = root / "demographics"
    if not subdir.exists():
        log.warning(
            "demographics subdir not found at %s — returning empty", subdir
        )
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "demographics expected file not found at %s — returning empty",
            csv_path,
        )
        return None
    return csv_path


__all__ = [
    "DEMOGRAPHICS_REQUIRED_COLUMNS_UN_WPP",
    "DEMOGRAPHICS_REQUIRED_COLUMNS_AFRICA",
    "load_un_wpp",
    "load_africa_2000_2023",
]
