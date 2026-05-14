"""Shared sidebar UI for the Mosaic Data Dashboard.

This helper exists because the locked Streamlit native ``pages/`` directory
pattern (D-15) does NOT support the entrypoint-widget persistence idiom — that
is ``st.navigation``-only. With ``pages/``, each page is its own top-level
script and ``app.py`` is NOT re-executed when the user clicks a sidebar page
link. The workaround is straightforward: render the sidebar via this shared
helper at the top of every page (and the entrypoint), keep the widget value in
``st.session_state`` so it survives page navigation, and let Streamlit auto-sync
the widget through its ``key=`` parameter.

Phase 1 ships a single widget here — the ephemeral data-root override (D-03).
Phase 2's country picker will land in this same module and reuse the pattern
(per RESEARCH.md §5 "Why this generalizes for Phase 2").

The function is intentionally NOT cached: UI re-renders on every Streamlit
script run, and the widget reads its current value from session_state every
time anyway.
"""

from __future__ import annotations

import streamlit as st

from mosaic_dashboard.config import SESSION_KEY


def render() -> None:
    """Render the shared sidebar. Call once per page (including the entrypoint).

    The data-root override is bound to ``st.session_state[SESSION_KEY]`` via
    the widget's ``key`` parameter — Streamlit reads the existing
    session_state value on each render, so the displayed value survives page
    navigation as long as this function is called on every page (P9
    mitigation: widgets not rendered on a given run have their state cleaned
    up at the end of that run).

    The session_state slot is initialized to an empty string before the widget
    renders if absent, so callers reading ``st.session_state[SESSION_KEY]``
    before the first widget render don't hit ``KeyError``. An empty string
    intentionally means "no override" — ``resolve_data_root()`` falls through
    to ``config.toml`` and then to the default.

    Returns:
        None. Side effect: renders sidebar widgets into the current Streamlit
        script run.
    """
    st.sidebar.header("Mosaic Dashboard")

    # P9 mitigation: initialize the session_state slot BEFORE the widget
    # renders, so reads of `st.session_state[SESSION_KEY]` from any page (even
    # before the widget itself runs on that page) never hit KeyError. We
    # deliberately store the empty string rather than `None` because
    # `resolve_data_root()` treats falsy values as "no override".
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = ""

    st.sidebar.text_input(
        "Data root override (session only)",
        key=SESSION_KEY,
        placeholder="Leave blank to use config.toml or default (~/MOSAIC/MOSAIC-data/processed)",
        help=(
            "Ephemeral override for this browser session. Does NOT persist "
            "to config.toml. Resolution order: this field → config.toml → "
            "default."
        ),
    )
