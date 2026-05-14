"""SSA Map page — clickable Sub-Saharan Africa choropleth (D-21, D-34).

Renders the ``AFRICA_ADM0`` outline via folium + streamlit-folium. Clicking a
country writes its ISO3 to ``st.session_state[COUNTRY_SESSION_KEY]`` — the
same slot the sidebar selectbox in ``ui/sidebar.py`` writes to (D-32, D-36).
Bidirectional sync between the dropdown and the map is implicit: both inputs
read from and write to the same session_state key (D-37). No callback
chaining, no event bus — just Streamlit's standard rerun cycle.

This file is autodiscovered by Streamlit's ``pages/`` directory pattern
(D-15, CLAUDE.md §4). The ``01_`` prefix sorts it after ``00_Data_Status``
in the sidebar; Streamlit converts the filename to the display label
``"SSA Map"`` and the URL ``/SSA_Map``.

Accessibility note: the folium iframe is NOT screen-reader-friendly (Leaflet
limitation; we can't patch ARIA labels into content we don't own). Users on
assistive tech fall back to the sidebar country selectbox — both inputs
write to the same ``st.session_state[COUNTRY_SESSION_KEY]`` slot, so the
map is a convenience layer, not the only path to selecting a country
(UI-SPEC Accessibility).

Three RESEARCH-mandated pitfall mitigations are encoded here:

1. **RESEARCH P7 — DBF column is ``iso_a3`` (lowercase, underscore).** The
   Natural Earth Admin-0 schema underlying ``AFRICA_ADM0.dbf`` uses the
   ``iso_a3`` form, NOT ``ISO3`` or ``ADM0_A3``. Every property access here
   uses ``properties["iso_a3"]`` — getting the case wrong silently breaks
   the choropleth highlighting AND the click handler.
2. **RESEARCH P10 — validate clicked ISO3 against ``country_metadata.ISO3_SET``
   before writing session_state.** ``AFRICA_ADM0.dbf`` ships two rows that
   are NOT in our picker's 54-entry set: ``ESH`` (Western Sahara) and
   ``"-99"`` (Somaliland — the literal sentinel string). Writing either to
   session_state crashes the sidebar selectbox on next render because the
   value isn't in ``options``. The membership check below is non-negotiable.
3. **RESEARCH P3 — narrow the rerun payload via ``returned_objects``.**
   Passing ``returned_objects=["last_active_drawing"]`` to ``st_folium``
   slims the JSON payload that streamlit-folium ships back from the
   iframe AND prevents pan/zoom interactions from triggering page reruns
   (only clicks land in ``last_active_drawing``).

Page-shell pattern (UI-SPEC, inherited from ``00_Data_Status``):
``set_page_config`` -> ``render_sidebar()`` -> imports -> title -> subtitle
-> selected-caption -> body -> trailing caption.
"""

from __future__ import annotations

import streamlit as st

# 1. set_page_config MUST be the first Streamlit call on the page (UI-SPEC
# Page-Shell Pattern). Browser-tab title; layout="wide" gives the map the
# full viewport width Streamlit allows.
st.set_page_config(page_title="SSA Map", layout="wide")

# 2. Render the shared sidebar BEFORE any other content — Phase 1 P9
# mitigation: widgets not rendered on a given run have their session_state
# pruned at end-of-run. Calling render_sidebar() on every page keeps both
# the data-root override and the country picker alive across navigation.
from mosaic_dashboard.ui.sidebar import render as render_sidebar  # noqa: E402

render_sidebar()

# 3. Remaining imports. All are `# noqa: E402` because the set_page_config +
# render_sidebar idiom above MUST run before module-level imports that
# touch Streamlit state — this matches the codebase convention established
# in 00_Data_Status.py.
import folium  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from mosaic_dashboard.config import COUNTRY_SESSION_KEY  # noqa: E402
from mosaic_dashboard.data import country_metadata, shapefiles  # noqa: E402
from mosaic_dashboard.data.errors import SchemaMismatchError  # noqa: E402

# 4. Page title — Display role (UI-SPEC Typography).
st.title("SSA Map")

# 5. One-sentence subtitle — Body role (UI-SPEC Map page copy).
st.write(
    "Click a country to select it, or use the Country picker in the sidebar."
)

# 6. Currently-selected indicator — Label role (UI-SPEC Map page copy).
# `.get()` (not `[]`) is defensive: render_sidebar() seeds the key on first
# load (D-33), but `.get()` protects against the empty-metadata edge case
# where the sidebar bailed early before seeding the slot.
selected_iso3 = st.session_state.get(COUNTRY_SESSION_KEY)
if selected_iso3:
    st.caption(
        f"Selected: {country_metadata.name_for(selected_iso3)} ({selected_iso3})"
    )

# 7. Load SSA geometry. Empty-state and schema-mismatch handling per D-39 /
# UI-SPEC "Empty / error states". A missing shapefile is the recoverable
# warning path; a malformed DBF (required column absent) is the loud-error
# path — both stop the page before any folium render is attempted.
try:
    africa = shapefiles.load_africa_geometry()
except SchemaMismatchError:
    st.error(
        "SSA shapefile is malformed (expected ISO3 attribute missing). "
        "See logs for details."
    )
    st.stop()

if africa.empty:
    st.warning(
        "SSA shapefile not found. Check Data Status, or set the data-root override in the sidebar."
    )
    st.stop()

# 8. Slim the GeoDataFrame to the three columns folium actually needs
# (RESEARCH P5). The full AFRICA_ADM0 GeoDataFrame carries 165 Natural
# Earth columns; passing all of them to folium.GeoJson balloons the
# serialized JSON payload by roughly 10x. Restricting to
# ["iso_a3", "name", "geometry"] yields ~30 KB total for 54 features.
africa_slim = africa[["iso_a3", "name", "geometry"]]

# 9. Build the folium map. CartoDB Positron tiles per UI-SPEC — light,
# neutral, doesn't fight the choropleth fills; free, no API key, folium
# auto-renders the OSM/CartoDB attribution badge (license requirement —
# do NOT hide it). Center is roughly the SSA centroid; zoom bounds keep
# the user from dragging off-continent or zooming past country-polygon
# resolution (Phase 5 LAYER-06 is the per-country zoom path).
m = folium.Map(
    location=[0.0, 20.0],  # UI-SPEC Projection, center, zoom
    zoom_start=3,
    tiles="CartoDB Positron",
    min_zoom=2,
    max_zoom=7,
)


def _style_function(feature: dict) -> dict:
    """Return the per-feature Leaflet style dict (UI-SPEC Country geometry styling).

    Reads the ISO3 from the GeoJson feature properties and compares against
    the page-scoped ``selected_iso3`` (captured at script-run time — see
    P8 note below). Selected country gets the accent red fill + dark-red
    stroke + 3px stroke width; everything else uses the neutral gray
    secondary fill + 1px stroke. Stroke-width contrast is the redundant
    selection signal for users with red/green color-vision difference
    (UI-SPEC Accessibility).

    Args:
        feature: GeoJSON feature dict supplied by folium.GeoJson per
            polygon. We read ``feature["properties"]["iso_a3"]``.

    Returns:
        Leaflet style dict with ``fillColor``, ``color``, ``weight``,
        ``fillOpacity`` keys (the four Leaflet expects).
    """
    # AFRICA_ADM0.dbf is Natural Earth schema; ISO3 column is 'iso_a3' (RESEARCH P7).
    iso3 = feature.get("properties", {}).get("iso_a3")
    if iso3 == selected_iso3:
        return {
            "fillColor": "#FF4B4B",  # Accent (Streamlit primary)
            "color": "#B71C1C",  # darker red stroke
            "weight": 3,
            "fillOpacity": 0.6,
        }
    return {
        "fillColor": "#F0F2F6",  # Secondary (Streamlit sidebar gray)
        "color": "#9AA0A6",  # neutral gray stroke
        "weight": 1,
        "fillOpacity": 0.7,
    }


def _highlight_function(feature: dict) -> dict:
    """Return the hover style for a feature (UI-SPEC Country geometry styling, hover row).

    Inherits the base state's style and brightens it slightly: +0.1
    ``fillOpacity`` (capped at 1.0) and +1 ``weight``. This makes hover
    feedback visible WITHOUT changing color — preserves the
    color-vs-stroke-width accessibility redundancy.
    """
    base = _style_function(feature)
    return {
        **base,
        "fillOpacity": min(base["fillOpacity"] + 0.1, 1.0),
        "weight": base["weight"] + 1,
    }


# 10. Add the GeoJson layer. ``tooltip`` is the one-line country name on
# hover (UI-SPEC Tooltip behavior); ``labels=False`` + ``aliases=[""]``
# together suppress the default "name: Angola" field-name prefix so the
# tooltip reads just "Angola" (RESEARCH P6).
folium.GeoJson(
    data=africa_slim,  # geopandas GeoDataFrame — folium calls .to_json() internally
    name="SSA countries",
    style_function=_style_function,
    highlight_function=_highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["name"],
        aliases=[""],
        labels=False,
        sticky=False,
    ),
).add_to(m)

# 11. Render via streamlit-folium. ``height=600`` is the UI-SPEC-locked
# pixel value — the folium iframe needs a concrete pixel height (RESEARCH
# P4; percentages do not work). ``use_container_width=True`` + ``width=None``
# together signal "fill the parent block" (streamlit-folium 0.27 idiom).
output = st_folium(
    m,
    key="ssa_map",
    width=None,
    height=600,
    use_container_width=True,
    # Slim rerun payload; pan/zoom does not trigger reruns (RESEARCH P3).
    returned_objects=["last_active_drawing"],
)

# 12. Click handler — write the clicked ISO3 to session_state if and only
# if it is a valid country in our picker's set AND differs from the
# currently-selected ISO3 (D-32, D-36, D-37). The next rerun makes the
# sidebar selectbox AND the map highlight reflect the new selection
# automatically — bidirectional sync is implicit in the shared session_state
# key, with no callback chaining required.
clicked = output.get("last_active_drawing") if output else None
if clicked and clicked.get("properties"):
    # AFRICA_ADM0.dbf is Natural Earth schema; ISO3 column is 'iso_a3' (RESEARCH P7).
    clicked_iso3 = clicked["properties"].get("iso_a3")
    # Validate against country_metadata.ISO3_SET — ESH (Western Sahara) and
    # "-99" (Somaliland) are in the DBF but NOT in our picker's set; silently
    # ignore clicks on them (RESEARCH P10).
    if (
        clicked_iso3
        and clicked_iso3 in country_metadata.ISO3_SET
        and clicked_iso3 != selected_iso3
    ):
        st.session_state[COUNTRY_SESSION_KEY] = clicked_iso3
        # Belt-and-suspenders: streamlit-folium fires its own rerun on click,
        # but an explicit st.rerun() guarantees the highlight + sidebar
        # update within this same interaction (RESEARCH Open Question 2;
        # Phase 6 PERF can revisit if the double-rerun cost matters).
        st.rerun()

# 13. Attribution caption below the map — license requirement for both the
# CartoDB Positron tiles (CC BY 3.0) and the AFRICA_ADM0 geometries
# (MOSAIC-data provenance). UI-SPEC Map page copy.
st.caption(
    "Geometries: MOSAIC-data/processed/shapefiles/AFRICA_ADM0. Tiles: CartoDB Positron / OpenStreetMap."
)
