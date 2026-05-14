"""Mosaic Data Dashboard — Streamlit entrypoint.

Phase 1 lands the user on a brief welcome screen and exposes the Data Status
page via the auto-discovered ``pages/`` sidebar. The Data Status page is the
only visible surface in Phase 1; Phases 2-7 layer additional pages on top of
this foundation.

Launch contract (D-17, CLAUDE.md §1):

    uv sync && uv run streamlit run src/mosaic_dashboard/app.py

Bare ``streamlit run`` and bare ``python -m streamlit ...`` are intentionally
NOT supported — they bypass the editable install of the ``mosaic_dashboard``
package and break absolute imports from ``pages/`` scripts.

Order of top-level Streamlit calls below matters:

1. ``st.set_page_config(...)`` MUST be the very first Streamlit call per the
   Streamlit API contract.
2. Logging configuration must run before any module that calls
   ``logging.getLogger(...).warning(...)`` produces output — but it's also
   idempotent across reruns, so re-entry on every script run is safe.
3. ``render_sidebar()`` runs on every page (RESEARCH.md §5) — not just the
   entrypoint — and the entrypoint is no exception. The shared helper writes
   the override slot into ``st.session_state`` so the page widget survives
   navigation.

No ``if __name__ == "__main__":`` guard — Streamlit imports this script
directly on every rerun (RESEARCH.md §"Streamlit Multi-Page Conventions"),
so top-level code runs on every rerun by design.
"""

from __future__ import annotations

import tomllib

import streamlit as st

from mosaic_dashboard.config import CONFIG_TOML_PATH
from mosaic_dashboard.logging_config import configure as configure_logging
from mosaic_dashboard.ui.sidebar import render as render_sidebar

# 1. set_page_config MUST be the first Streamlit call. Per CLAUDE.md no-emoji
# policy, page_icon is omitted (Streamlit falls back to its own default).
st.set_page_config(
    page_title="Mosaic Data Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _read_log_level() -> str:
    """Read ``[logging] level`` from the repo-root config.toml.

    Returns:
        Log level string (defaults to ``"INFO"``) if the file is missing or
        the key is absent. Falls back gracefully so a fresh clone without a
        committed ``config.toml`` still launches.
    """
    if not CONFIG_TOML_PATH.exists():
        return "INFO"
    with CONFIG_TOML_PATH.open("rb") as f:
        cfg = tomllib.load(f)
    return str(cfg.get("logging", {}).get("level", "INFO")).strip() or "INFO"


# 2. Configure stdlib logging (idempotent — safe to call on every rerun).
configure_logging(_read_log_level())

# 3. Render the shared sidebar (per RESEARCH.md §5: every page, including the
# entrypoint, calls this — keeps the data-root override widget alive across
# navigation).
render_sidebar()

# 4. Welcome body. Phase 1's only visible surface is the Data Status page; the
# entrypoint just orients the user.
st.title("Mosaic Data Dashboard")
st.write(
    "Inspect the MOSAIC-data/processed/ datasets layer by layer. "
    "Start with **Data Status** in the sidebar to verify your local checkout."
)
