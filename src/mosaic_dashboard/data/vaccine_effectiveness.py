"""Vaccine-effectiveness loader — stub-with-discovery for Phase 1.

Single global decay curve from published studies (effectiveness vs. days
post-vaccination). Like immunity, this is NOT country-scoped — the
`country` parameter is a contract placeholder for API uniformity.

Phase 1 contract: public API surface is locked; Phase 5 will decide the
final reshape / metadata-filter approach. Plan 05's Data Status page handles
file enumeration generically via `Path.glob`, not by calling this module.

Empty-state contract (D-08, D-10, D-13): same as immunity / big-five.
Cache contract (D-18, D-20): public/private split, mtime-keyed, reversible
internals.

Upstream column names sourced from `COLUMN_DISCOVERY.md` §vaccine_effectiveness.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

#: Required columns from `vaccine_effectiveness_data.csv` (post-load). Phase
#: 5 may extend this set if it adds a rename map.
VACCINE_EFFECTIVENESS_REQUIRED_COLUMNS: set[str] = {
    "day",
    "effectiveness",
    "effectiveness_hi",
    "effectiveness_lo",
    "day_min",
    "day_max",
    "source",
}

_VE_FILENAME = "vaccine_effectiveness_data.csv"


def load(country: str | None = None) -> pd.DataFrame:
    """Load the vaccine-effectiveness curve.

    Args:
        country: Currently unused — data is global per source. Kept for API
            uniformity. Phase 5 may give this argument semantics.

    Returns:
        DataFrame with canonical columns ``{day, effectiveness,
        effectiveness_hi, effectiveness_lo, day_min, day_max, source}``.
        Empty (canonical columns, zero rows) when the
        `vaccine_effectiveness/` subdir is missing or the expected CSV is
        absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    csv_path = _resolve_ve_csv(_VE_FILENAME)
    if csv_path is None:
        return _empty()
    mtime = csv_path.stat().st_mtime
    return _read_ve_cached(str(csv_path), mtime).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_ve_cached(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(
        df,
        VACCINE_EFFECTIVENESS_REQUIRED_COLUMNS,
        dataset="vaccine_effectiveness",
    )
    return df


def _empty() -> pd.DataFrame:
    return pd.DataFrame(
        {
            c: pd.Series(dtype="object")
            for c in VACCINE_EFFECTIVENESS_REQUIRED_COLUMNS
        }
    )


def _resolve_ve_csv(filename: str) -> Path | None:
    root = resolve_data_root()
    subdir = root / "vaccine_effectiveness"
    if not subdir.exists():
        log.warning(
            "vaccine_effectiveness subdir not found at %s — returning empty",
            subdir,
        )
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "vaccine_effectiveness expected file not found at %s — returning empty",
            csv_path,
        )
        return None
    return csv_path


__all__ = [
    "VACCINE_EFFECTIVENESS_REQUIRED_COLUMNS",
    "load",
]
