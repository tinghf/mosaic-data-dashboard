"""Data Status page — Phase 1's only visible surface.

Enumerates every expected ``processed/`` subdir (D-11) and shows presence,
file count, and most-recent mtime per row. This is the one place where data
layer state translates into browser-visible UI via ``st.warning`` /
``st.error`` / ``st.info`` (per RESEARCH.md §"logging.warning vs st.warning":
loaders log to stderr; the Data Status page paints user-visible banners).

Filename convention: zero-padded ``00_`` prefix per P1 (Streamlit sorts the
numeric prefix as int, so ``00_`` sorts before ``01_`` and stays first in the
sidebar even as Phase 2+ pages land alongside it).

Top-of-file call order (strict):

1. ``import streamlit as st``
2. ``st.set_page_config(...)`` — per-page browser-tab title override.
3. ``from mosaic_dashboard.ui.sidebar import render as render_sidebar`` then
   call ``render_sidebar()`` — MUST run on every page per RESEARCH.md §5 to
   keep the override widget alive across navigation (P9 mitigation).
4. Remaining imports (after the sidebar render).

This is a page script, not a module — page files run as top-level scripts.
Use ABSOLUTE imports (``from mosaic_dashboard.xxx import ...``); relative
imports do not work in pages/ (RESEARCH.md gotcha 4).

Caching note: ``_subdir_status`` is intentionally NOT decorated with
``@st.cache_data``. DATA-02 requires the mtime column to update on the very
next page interaction after a CSV edit; caching would defeat that. The stat
calls are cheap (O(1) per file).
"""

from __future__ import annotations

import streamlit as st

# 1. set_page_config must precede any other Streamlit call on this page.
st.set_page_config(page_title="Data Status", layout="wide")

# 2. Render the shared sidebar before any other content so the data-root
# override widget is alive on this page (RESEARCH.md §5, P9).
from mosaic_dashboard.ui.sidebar import render as render_sidebar  # noqa: E402

render_sidebar()

# 3. Remaining imports (after set_page_config + render_sidebar so the linter
# noqa above is the only late-import we need).
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

import pandas as pd  # noqa: E402

from mosaic_dashboard.config import resolve_data_root  # noqa: E402
from mosaic_dashboard.data import shapefiles  # noqa: E402

#: The 12 subdir paths Phase 1 enumerates (D-11, RESEARCH.md interfaces). WHO
#: is broken into its three time granularities so a partial-WHO scenario
#: (e.g., upstream renames just ``WHO/daily/``) shows the granular row as
#: MISSING while the others still show OK. Order here drives table row order.
EXPECTED_SUBDIRS: list[str] = [
    "WHO/annual",
    "WHO/weekly",
    "WHO/daily",
    "WASH",
    "ENSO",
    "demographics",
    "OAG",
    "shapefiles",
    "immunity",
    "vaccine_effectiveness",
    "symptomatic",
    "similarity_matrix",
]


def _subdir_status(root: Path, subdir_rel: str) -> dict[str, Any]:
    """Return one row of presence/file-count/mtime metadata for a subdir.

    Args:
        root: Resolved data-root path (from ``resolve_data_root()``).
        subdir_rel: Relative path under ``root`` (e.g., ``"WHO/annual"`` or
            ``"WASH"``).

    Returns:
        A dict with the keys the Data Status table renders:

            subdir              -- the relative path passed in (unchanged)
            status              -- "OK" | "EMPTY" | "MISSING" | "INVALID"
            file_count          -- count of regular files directly in the subdir
            latest_mtime        -- ISO-8601 string with second precision, or "—"
            latest_mtime_epoch  -- float seconds-since-epoch, or None

        Status semantics:
            MISSING -- path does not exist
            INVALID -- path exists but is not a directory (upstream replaced
                       the expected directory with a file)
            EMPTY   -- directory exists but has zero regular files
            OK      -- directory has one or more regular files
    """
    path = root / subdir_rel

    if not path.exists():
        return {
            "subdir": subdir_rel,
            "status": "MISSING",
            "file_count": 0,
            "latest_mtime": "—",
            "latest_mtime_epoch": None,
        }

    if not path.is_dir():
        return {
            "subdir": subdir_rel,
            "status": "INVALID",
            "file_count": 0,
            "latest_mtime": "—",
            "latest_mtime_epoch": None,
        }

    # Direct children that are regular files (excludes subdirectories so the
    # WHO/ aggregate parent doesn't double-count its granularity buckets).
    files = [p for p in path.iterdir() if p.is_file()]
    file_count = len(files)

    if file_count == 0:
        return {
            "subdir": subdir_rel,
            "status": "EMPTY",
            "file_count": 0,
            "latest_mtime": "—",
            "latest_mtime_epoch": None,
        }

    latest_epoch = max(f.stat().st_mtime for f in files)
    latest_iso = datetime.fromtimestamp(latest_epoch).isoformat(timespec="seconds")
    return {
        "subdir": subdir_rel,
        "status": "OK",
        "file_count": file_count,
        "latest_mtime": latest_iso,
        "latest_mtime_epoch": latest_epoch,
    }


st.title("Data Status")
st.write(
    "Verify that the MOSAIC-data/processed/ checkout is hooked up correctly. "
    "Each row is one expected subdirectory."
)

root = resolve_data_root()
st.caption(f"Resolved data root: `{root}`")

if not root.exists():
    st.error(
        f"Data root not found: {root}. Edit config.toml or use the sidebar "
        "override."
    )
    st.stop()

rows = [_subdir_status(root, s) for s in EXPECTED_SUBDIRS]
df = pd.DataFrame(rows)

st.dataframe(
    df[["subdir", "status", "file_count", "latest_mtime"]],
    use_container_width=True,
    hide_index=True,
)

# Per-status summary banners. Data Status is the ONE place loader state turns
# into UI (RESEARCH.md §"logging.warning vs st.warning").
missing = [r["subdir"] for r in rows if r["status"] == "MISSING"]
empty = [r["subdir"] for r in rows if r["status"] == "EMPTY"]
invalid = [r["subdir"] for r in rows if r["status"] == "INVALID"]

if missing:
    st.warning(
        f"Missing subdirs: {', '.join(missing)}. Loaders for these layers "
        "will return empty DataFrames."
    )
if empty:
    st.info(
        f"Empty subdirs: {', '.join(empty)}. Layer is present but contains "
        "no files."
    )
if invalid:
    st.error(
        f"Invalid path (not a directory): {', '.join(invalid)}."
    )

# Shapefile integration metric — confirms Plan 04's available_countries() is
# wired in; Phase 2's country picker will reuse the same call.
st.metric("Countries with shapefiles", len(shapefiles.available_countries()))
