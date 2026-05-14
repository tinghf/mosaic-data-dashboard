"""Immunity loader — stub-with-discovery for Phase 1.

Phase 1 contract: full public API surface is locked here so Plans 02–07 can
import and call these functions; the implementation is intentionally minimal
because the Phase 5 visualization will decide the final reshape / filter
shape. Plan 05's Data Status page only needs to know which CSV files are
present under `<root>/immunity/` — the per-file presence/file-count
enumeration happens generically in Data Status using `Path.glob`, NOT by
calling into this module.

Both files in this subdir (`immune_decay_data.csv`,
`immune_durability_data.csv`) are **global** decay/durability curves
(effectiveness vs. days since vaccination), not country-scoped. The
`country` parameter is currently a contract placeholder — it has no
filtering effect because the upstream data has no country column. Phase 5
may decide to use it for metadata filtering (e.g., by `source`).

Empty-state contract (D-08, D-10, D-13):
- Missing `immunity/` subdir or missing expected CSV → empty DataFrame +
  `logging.warning(...)`.
- File present, missing required columns → `SchemaMismatchError` (D-12).

Cache contract (D-18, D-20): public/private split; private reader is
`@st.cache_data`-decorated and keyed on (path, mtime). The internal cache
representation is reversible (D-20) — Phase 5 can change the rename / schema
without touching the public function signatures.

Upstream column names sourced from `COLUMN_DISCOVERY.md` §immunity.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from mosaic_dashboard.config import resolve_data_root
from mosaic_dashboard.data._schema import require_columns

log = logging.getLogger(__name__)

#: Required columns shared by both immunity CSVs (post-load). Phase 5 may
#: extend this set if it adds a rename map.
IMMUNITY_REQUIRED_COLUMNS: set[str] = {
    "day",
    "effectiveness",
    "effectiveness_hi",
    "effectiveness_lo",
    "source",
}

_DECAY_FILENAME = "immune_decay_data.csv"
_DURABILITY_FILENAME = "immune_durability_data.csv"


def load_decay(country: str | None = None) -> pd.DataFrame:
    """Load immune-decay curve (effectiveness vs. days since vaccination).

    Args:
        country: Currently unused — data is global per source. Argument is
            kept for API uniformity with country-scoped loaders. Phase 5 may
            give this argument semantics (e.g., filter by `source`).

    Returns:
        DataFrame with canonical columns ``{day, effectiveness,
        effectiveness_hi, effectiveness_lo, source}``. Empty (canonical
        columns, zero rows) when the `immunity/` subdir is missing or the
        expected CSV is absent.

    Raises:
        SchemaMismatchError: When the expected CSV is present but missing a
            required column.
    """
    return _load(_DECAY_FILENAME)


def load_durability(country: str | None = None) -> pd.DataFrame:
    """Load immune-durability curve. Same semantics as ``load_decay``."""
    return _load(_DURABILITY_FILENAME)


def _load(filename: str) -> pd.DataFrame:
    csv_path = _resolve_immunity_csv(filename)
    if csv_path is None:
        return _empty()
    mtime = csv_path.stat().st_mtime
    return _read_immunity_cached(str(csv_path), mtime).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _read_immunity_cached(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    require_columns(df, IMMUNITY_REQUIRED_COLUMNS, dataset="immunity")
    return df


def _empty() -> pd.DataFrame:
    return pd.DataFrame(
        {c: pd.Series(dtype="object") for c in IMMUNITY_REQUIRED_COLUMNS}
    )


def _resolve_immunity_csv(filename: str) -> Path | None:
    """Resolve ``<root>/immunity/<filename>``; warn + return None on miss.

    Same D-13 handling as the big-five: missing subdir AND missing expected
    file both warn-and-empty; schema mismatch raises.
    """
    root = resolve_data_root()
    subdir = root / "immunity"
    if not subdir.exists():
        log.warning("immunity subdir not found at %s — returning empty", subdir)
        return None
    csv_path = subdir / filename
    if not csv_path.exists():
        log.warning(
            "immunity expected file not found at %s — returning empty", csv_path
        )
        return None
    return csv_path


__all__ = [
    "IMMUNITY_REQUIRED_COLUMNS",
    "load_decay",
    "load_durability",
]
