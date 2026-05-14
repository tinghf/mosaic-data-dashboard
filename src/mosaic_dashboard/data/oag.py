"""OAG flight-mobility loaders.

Three granularities — daily, weekly, monthly — over the mean 2017
passenger-flow tables under `MOSAIC-data/processed/OAG/`.

**Bidirectional country filter.** OAG is the one loader in the project that
keeps TWO ISO3 columns (`origin_iso3`, `destination_iso3`) — flight mobility
is intrinsically pairwise. Per the Plan 03 contract (and Open Question #2 in
01-RESEARCH.md, resolved during plan revision), `country` filters rows where
the country appears as EITHER origin OR destination. Pass `country=None` to
get the full SSA flow table.

This is the documented exception to the "loaders normalize to a single
`country_iso3`" rule (D-07). Views downstream MUST handle both columns —
typical pattern: aggregate by `origin_iso3` when "flights out of country"
view is wanted, by `destination_iso3` for "flights into".

Empty-state contract (D-08, D-10, D-13):
- Missing `OAG/` subdir or missing expected CSV → empty DataFrame +
  `logging.warning(...)`.
- File present, missing required columns → `SchemaMismatchError` (D-12).
- Country absent from BOTH origin and destination → empty DataFrame.

Cache contract (D-18, D-20): public/private split; private reader is
`@st.cache_data`-decorated and keyed on (path, mtime). Country filter happens
OUTSIDE the cache (filtering after read is cheap; caching pre-filtered DFs
would explode cache keys to N_countries × 3 granularities).

Upstream column names sourced verbatim from `COLUMN_DISCOVERY.md` §OAG.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

#: Required columns (post-load) for all three granularities. OAG keeps both
#: ISO3 columns because flight mobility is pairwise (origin → destination).
#: See module docstring for the bidirectional-filter rationale.
OAG_REQUIRED_COLUMNS: set[str] = {
    "origin_iso3",
    "destination_iso3",
    "year",
    "count",
}

# Canonical filenames per COLUMN_DISCOVERY.md.
_OAG_DAILY_FILENAME = "oag_africa_2017_mean_daily.csv"
_OAG_WEEKLY_FILENAME = "oag_africa_2017_mean_weekly.csv"
_OAG_MONTHLY_FILENAME = "oag_africa_2017_mean_monthly.csv"


# --- Daily -----------------------------------------------------------------


def load_daily(country: str | None = None) -> pd.DataFrame:
    """Load daily mean OAG flight mobility, optionally bidirectionally filtered.

    Args:
        country: ISO3 country code. When ``None``, returns the full
            origin→destination table; when set, returns only rows where
            ``country`` appears as EITHER origin OR destination (D-08 returns
            empty when absent from both sides).

    Returns:
        DataFrame with canonical columns ``{origin_iso3, destination_iso3,
        year, count}``. Empty (canonical columns, zero rows) when the OAG
        subdir is missing, the expected CSV is absent, or the country is
        absent from both origin and destination columns.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column (D-12).
    """
    return _load(_OAG_DAILY_FILENAME, country)


# --- Weekly ----------------------------------------------------------------


def load_weekly(country: str | None = None) -> pd.DataFrame:
    """Load weekly mean OAG flight mobility, optionally bidirectionally filtered.

    See ``load_daily`` for argument/return semantics — same shape, different
    granularity.
    """
    return _load(_OAG_WEEKLY_FILENAME, country)


# --- Monthly ---------------------------------------------------------------


def load_monthly(country: str | None = None) -> pd.DataFrame:
    """Load monthly mean OAG flight mobility, optionally bidirectionally filtered.

    See ``load_daily`` for argument/return semantics — same shape, different
    granularity.
    """
    return _load(_OAG_MONTHLY_FILENAME, country)


# --- Shared core -----------------------------------------------------------


def _load(filename: str, country: str | None) -> pd.DataFrame:
    """Path resolution + cached read + bidirectional country filter."""
    csv_path = _resolve_oag_csv(filename)
    if csv_path is None:
        return _empty()
    mtime = csv_path.stat().st_mtime
    df = _read_oag_cached(str(csv_path), mtime)
    if country is not None:
        mask = (df["origin_iso3"] == country) | (df["destination_iso3"] == country)
        df = df[mask]
        if df.empty:
            return _empty()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_oag_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached OAG CSV read keyed on (path, mtime).

    No date parsing — OAG's `year` column is a single fixed integer (2017)
    per COLUMN_DISCOVERY.md.
    """
    df = pd.read_csv(path)
    require_columns(df, OAG_REQUIRED_COLUMNS, dataset="OAG")
    return df


def _empty() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in OAG_REQUIRED_COLUMNS}
    )


# --- Internal helper -------------------------------------------------------


def _resolve_oag_csv(filename: str) -> Path | None:
    """Resolve ``<root>/OAG/<filename>``; warn + return None on miss.

    Subdir absence and missing expected file are BOTH warned and treated as
    empty per D-13 (re-confirmed during plan revision). Only schema mismatch
    in a *present* file raises.
    """
    root = resolve_data_root()
    subdir = root / "OAG"
    if not subdir.exists():
        log.warning("OAG subdir not found at %s — returning empty", subdir)
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "OAG expected file not found at %s — returning empty", csv_path
        )
        return None
    return csv_path


__all__ = [
    "OAG_REQUIRED_COLUMNS",
    "load_daily",
    "load_weekly",
    "load_monthly",
]
