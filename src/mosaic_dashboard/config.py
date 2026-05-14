"""Configuration resolution for the dashboard's data root.

Implements the three-tier resolution order per D-04 (CONTEXT.md):

    1. Sidebar override (ephemeral, session-scoped) — D-03
    2. Repo-root `config.toml` `[data] root` — D-01
    3. Default: `~/MOSAIC/MOSAIC-data/processed/` — D-02

The function does NOT check that the resolved path exists — that's the Data
Status page's job (Plan 05). The function does NOT use `@st.cache_data` — TOML
reads are cheap and we want config-file edits to take effect on the next rerun
without manual cache-clearing.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import streamlit as st

#: Default data root per D-02 — matches the documented teammate convention.
DEFAULT_DATA_ROOT: Path = Path("~/MOSAIC/MOSAIC-data/processed").expanduser()

#: `st.session_state` slot the sidebar writes to (D-03). Plan 05's
#: `ui/sidebar.py` reads/writes this key via a `text_input` widget.
SESSION_KEY: str = "data_root_override"

#: Repo-root `config.toml` path. This file is at
#: `src/mosaic_dashboard/config.py`, so:
#:   parents[0] = src/mosaic_dashboard/
#:   parents[1] = src/
#:   parents[2] = repo root
CONFIG_TOML_PATH: Path = Path(__file__).resolve().parents[2] / "config.toml"


def resolve_data_root() -> Path:
    """Resolve the active data-root path per D-04.

    Resolution order (highest priority first):

    1. **Sidebar override** — `st.session_state[SESSION_KEY]`. A non-empty
       string here wins. An empty string means "no override" and falls
       through. (Ephemeral; not persisted to `config.toml`.)
    2. **Repo-root `config.toml`** — `[data].root` value (after `.strip()`).
       Only consulted if the file exists and the key is non-empty.
    3. **Default** — `DEFAULT_DATA_ROOT` (`~/MOSAIC/MOSAIC-data/processed/`).

    Returns:
        A `pathlib.Path`. Both override and config values are passed through
        `Path(...).expanduser()` so `~` works on every supported platform.
        The returned path is NOT validated for existence — callers (notably
        the Data Status page) check that separately.
    """
    # 1. Sidebar override (ephemeral, session-scoped, D-03)
    override = st.session_state.get(SESSION_KEY)
    if override:
        return Path(override).expanduser()

    # 2. Repo-root config.toml (D-01)
    if CONFIG_TOML_PATH.exists():
        with CONFIG_TOML_PATH.open("rb") as f:
            cfg = tomllib.load(f)
        configured = cfg.get("data", {}).get("root", "").strip()
        if configured:
            return Path(configured).expanduser()

    # 3. Default (D-02)
    return DEFAULT_DATA_ROOT
