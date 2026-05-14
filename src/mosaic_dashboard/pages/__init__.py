"""Streamlit multi-page navigation root.

Streamlit auto-discovers ``.py`` files directly under this directory (NOT
subdirectories) and renders them as sidebar links per the rules documented in
RESEARCH.md §"Streamlit Multi-Page Conventions". Filenames use a two-digit
zero-padded numeric prefix for stable sort order (P1 mitigation):

    pages/00_Data_Status.py     → sidebar label "Data Status", URL /Data_Status
    pages/01_Country_Picker.py  → (future Phase 2)

Page modules are executed by Streamlit as top-level scripts, not imported as
modules — they must use ABSOLUTE imports (``from mosaic_dashboard.config
import ...``) rather than relative imports (RESEARCH.md gotcha 4).
"""
