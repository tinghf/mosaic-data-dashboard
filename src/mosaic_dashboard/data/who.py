"""WHO cholera-case loaders.

Three granularities — annual, weekly, daily — each shipped as a public
`load_*(country)` function plus a private `@st.cache_data`-decorated reader and
an empty-DataFrame factory. Reference implementation per RESEARCH.md §4 / D-05.

Empty-state contract (D-08, D-10, D-13):
- Missing `WHO/`, missing granularity subdir, or missing expected CSV →
  return empty DataFrame with canonical columns AND emit `logging.warning(...)`.
- File present but missing required columns → `SchemaMismatchError` (D-12).
- Country filter applied OUTSIDE the cache; absent country → empty DataFrame.

Cache contract (D-18, D-20):
- Disk reads are wrapped in `@st.cache_data(show_spinner=False)` keyed on
  `(path: str, mtime: float)` per RESEARCH.md §4 pitfall P7. Public/private
  split keeps cache representation reversible without breaking the API.

Upstream column names sourced from `COLUMN_DISCOVERY.md`. Loaders own the
rename to canonical (`country_iso3`) per D-06/D-07.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

# --- Required-column sets (post-rename, per COLUMN_DISCOVERY.md) -----------

#: Annual cholera cases (WHO AFRO 1949–2024). Canonical columns enforced
#: after the upstream `iso_code` → `country_iso3` rename.
WHO_REQUIRED_COLUMNS_ANNUAL: set[str] = {
    "country_iso3",
    "year",
    "cases_total",
    "deaths_total",
    "cfr",
}

#: Weekly cholera cases (cholera_country_weekly_processed.csv). `date_start`
#: and `date_stop` are ISO-8601 dates parsed at read time.
WHO_REQUIRED_COLUMNS_WEEKLY: set[str] = {
    "country_iso3",
    "year",
    "week",
    "date_start",
    "date_stop",
    "cases",
    "deaths",
}

#: Daily cholera cases (cholera_country_daily_processed.csv).
WHO_REQUIRED_COLUMNS_DAILY: set[str] = {
    "country_iso3",
    "date",
    "cases",
    "deaths",
}

# Canonical filenames per COLUMN_DISCOVERY.md (primary file per granularity).
_WHO_ANNUAL_FILENAME = "who_afro_annual_1949_2024.csv"
_WHO_WEEKLY_FILENAME = "cholera_country_weekly_processed.csv"
_WHO_DAILY_FILENAME = "cholera_country_daily_processed.csv"


# --- Annual ----------------------------------------------------------------


def load_annual(country: str | None = None) -> pd.DataFrame:
    """Load WHO annual cholera cases, optionally filtered to one ISO3 country.

    Args:
        country: ISO3 country code (e.g., "AGO"). When ``None``, returns the
            full table; when set, returns only rows where
            ``country_iso3 == country`` (empty DataFrame if the country is
            absent — D-08).

    Returns:
        DataFrame with canonical columns ``{country_iso3, year, cases_total,
        deaths_total, cfr}`` (extras tolerated). Empty (canonical columns,
        zero rows) when the WHO/annual subdir is missing, the expected CSV is
        missing, or the country is absent (D-08, D-10, D-13).

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column (D-12). Not cached — re-raises until the file is
            fixed (RESEARCH.md §8 P8).
    """
    root = resolve_data_root()
    subdir = root / "WHO" / "annual"
    if not subdir.exists():
        log.warning("WHO/annual subdir not found at %s — returning empty", subdir)
        return _empty_annual()
    csv_path = subdir / _WHO_ANNUAL_FILENAME
    if not csv_path.exists():
        # Fall back to any CSV in the subdir (lenient on file additions per
        # D-13) so an upstream rename of the primary file still resolves.
        candidates = sorted(subdir.glob("*.csv"))
        if not candidates:
            log.warning(
                "WHO/annual has no CSV files (looked for %s) — returning empty",
                csv_path,
            )
            return _empty_annual()
        csv_path = candidates[0]
    mtime = csv_path.stat().st_mtime
    df = _read_who_annual_cached(str(csv_path), mtime)
    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_annual()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_who_annual_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached annual-CSV read keyed on (path, mtime).

    The ``mtime`` argument participates in Streamlit's cache key — when the
    file's mtime changes, the cache misses and the file is re-read (D-18).
    SchemaMismatchError raised here is **not** cached (P8); it re-raises on
    every call until the file is fixed and mtime changes.
    """
    df = pd.read_csv(path)
    df = df.rename(columns={"iso_code": "country_iso3"})
    require_columns(df, WHO_REQUIRED_COLUMNS_ANNUAL, dataset="WHO/annual")
    return df


def _empty_annual() -> pd.DataFrame:
    """Canonical empty DataFrame for WHO/annual (D-08 shape guarantee)."""
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in WHO_REQUIRED_COLUMNS_ANNUAL}
    )


# --- Weekly ----------------------------------------------------------------


def load_weekly(country: str | None = None) -> pd.DataFrame:
    """Load WHO weekly cholera cases, optionally filtered to one ISO3 country.

    Args:
        country: ISO3 country code (e.g., "AGO"). When ``None``, returns the
            full table; when set, returns only rows where
            ``country_iso3 == country`` (empty DataFrame if absent — D-08).

    Returns:
        DataFrame with canonical columns ``{country_iso3, year, week,
        date_start, date_stop, cases, deaths}``. Empty (canonical columns,
        zero rows) when the WHO/weekly subdir is missing, the expected CSV is
        missing, or the country is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    root = resolve_data_root()
    subdir = root / "WHO" / "weekly"
    if not subdir.exists():
        log.warning("WHO/weekly subdir not found at %s — returning empty", subdir)
        return _empty_weekly()
    csv_path = subdir / _WHO_WEEKLY_FILENAME
    if not csv_path.exists():
        candidates = sorted(subdir.glob("*.csv"))
        if not candidates:
            log.warning(
                "WHO/weekly has no CSV files (looked for %s) — returning empty",
                csv_path,
            )
            return _empty_weekly()
        csv_path = candidates[0]
    mtime = csv_path.stat().st_mtime
    df = _read_who_weekly_cached(str(csv_path), mtime)
    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_weekly()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_who_weekly_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached weekly-CSV read keyed on (path, mtime)."""
    df = pd.read_csv(path, parse_dates=["date_start", "date_stop"])
    df = df.rename(columns={"iso_code": "country_iso3"})
    require_columns(df, WHO_REQUIRED_COLUMNS_WEEKLY, dataset="WHO/weekly")
    return df


def _empty_weekly() -> pd.DataFrame:
    """Canonical empty DataFrame for WHO/weekly."""
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in WHO_REQUIRED_COLUMNS_WEEKLY}
    )


# --- Daily -----------------------------------------------------------------


def load_daily(country: str | None = None) -> pd.DataFrame:
    """Load WHO daily cholera cases, optionally filtered to one ISO3 country.

    Args:
        country: ISO3 country code (e.g., "AGO"). When ``None``, returns the
            full table; when set, returns only rows where
            ``country_iso3 == country`` (empty DataFrame if absent — D-08).

    Returns:
        DataFrame with canonical columns ``{country_iso3, date, cases,
        deaths}``. Empty (canonical columns, zero rows) when the WHO/daily
        subdir is missing, the expected CSV is missing, or the country is
        absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    root = resolve_data_root()
    subdir = root / "WHO" / "daily"
    if not subdir.exists():
        log.warning("WHO/daily subdir not found at %s — returning empty", subdir)
        return _empty_daily()
    csv_path = subdir / _WHO_DAILY_FILENAME
    if not csv_path.exists():
        candidates = sorted(subdir.glob("*.csv"))
        if not candidates:
            log.warning(
                "WHO/daily has no CSV files (looked for %s) — returning empty",
                csv_path,
            )
            return _empty_daily()
        csv_path = candidates[0]
    mtime = csv_path.stat().st_mtime
    df = _read_who_daily_cached(str(csv_path), mtime)
    if country is not None:
        df = df[df["country_iso3"] == country]
        if df.empty:
            return _empty_daily()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_who_daily_cached(path: str, mtime: float) -> pd.DataFrame:
    """Cached daily-CSV read keyed on (path, mtime)."""
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.rename(columns={"iso_code": "country_iso3"})
    require_columns(df, WHO_REQUIRED_COLUMNS_DAILY, dataset="WHO/daily")
    return df


def _empty_daily() -> pd.DataFrame:
    """Canonical empty DataFrame for WHO/daily."""
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in WHO_REQUIRED_COLUMNS_DAILY}
    )


__all__ = [
    "WHO_REQUIRED_COLUMNS_ANNUAL",
    "WHO_REQUIRED_COLUMNS_WEEKLY",
    "WHO_REQUIRED_COLUMNS_DAILY",
    "load_annual",
    "load_weekly",
    "load_daily",
]
