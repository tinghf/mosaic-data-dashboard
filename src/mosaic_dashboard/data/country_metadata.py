"""Static ISO3 -> name lookup for the SSA country picker (D-24..D-29).

This module is the single source of truth for country names shown in the
picker. It is intentionally NOT generated from ``AFRICA_ADM0.dbf`` -- the DBF
ships Natural Earth labels which are sometimes long-form (``"Cote d'Ivoire"``,
``"S. Sudan"``) or include disputed-territory rows we don't want in the picker
(Western Sahara, Somaliland). Editing this list is the canonical way to
change picker order, picker default, or naming.

Order matters (D-25): the iteration order IS the picker display order, and
the first entry IS the first-load default (D-26). Ships alphabetical-by-name
with Angola first (D-27).

Cross-referenced with ``shapefiles.available_countries()`` at startup (D-29):
:func:`warn_if_drifted_from_shapefiles` emits a single warning if the
metadata set and the shapefile set diverge. The helper never raises -- per
D-29, divergence is tolerated (D-04 spirit).

Public surface:

- :data:`COUNTRIES` -- ordered tuple of ``(iso3, name)`` pairs, 54 entries.
- :data:`ISO3_SET` -- frozenset of the 54 valid ISO3 codes; used by the
  click handler in Plan 02-04 to guard against the ESH/-99 DBF leak.
- :func:`iter_countries` -- list-copy of :data:`COUNTRIES` for the sidebar
  selectbox options.
- :func:`name_for` -- ISO3 -> display name lookup; returns the input ISO3
  unchanged for unknown codes (never raises).
- :func:`warn_if_drifted_from_shapefiles` -- one-call startup drift check.

Per D-05/D-28 this module sits next to the per-subdir loaders under
``data/`` but is itself NOT a per-subdir loader -- it reads no files from
``MOSAIC-data/processed/``. It carries only the two columns mandated by
D-28 (iso3 + name); region/population/etc. are deferred until a downstream
phase actually needs them.
"""

from __future__ import annotations

import logging
from typing import Iterable

log = logging.getLogger(__name__)

#: Ordered tuple of ``(ISO3, display name)`` pairs. The iteration order IS
#: the picker order (D-25); the first entry IS the first-load default (D-26).
#: Ships alphabetical-by-name with Angola first (D-27); edit freely to
#: reorder the picker or change the default.
#:
#: Names follow MOSAIC project convention: short, common forms -- not the
#: Natural Earth long-form. Reviewed against Natural Earth ``name`` column;
#: 8 deviations from the DBF text are noted inline.
COUNTRIES: tuple[tuple[str, str], ...] = (
    ("AGO", "Angola"),
    ("DZA", "Algeria"),
    ("BEN", "Benin"),
    ("BWA", "Botswana"),
    ("BFA", "Burkina Faso"),
    ("BDI", "Burundi"),
    ("CPV", "Cabo Verde"),
    ("CMR", "Cameroon"),
    ("CAF", "Central African Republic"),   # DBF: "Central African Rep." -- expanded
    ("TCD", "Chad"),
    ("COM", "Comoros"),
    ("COG", "Republic of the Congo"),       # DBF: "Congo" -- long form disambiguates from COD
    ("COD", "Democratic Republic of the Congo"),  # DBF: "Dem. Rep. Congo" -- expanded
    ("CIV", "Côte d'Ivoire"),
    ("DJI", "Djibouti"),
    ("EGY", "Egypt"),
    ("GNQ", "Equatorial Guinea"),           # DBF: "Eq. Guinea" -- expanded
    ("ERI", "Eritrea"),
    ("SWZ", "Eswatini"),                    # DBF: "eSwatini"; ISO 3166 spelling "Eswatini"
    ("ETH", "Ethiopia"),
    ("GAB", "Gabon"),
    ("GMB", "Gambia"),
    ("GHA", "Ghana"),
    ("GIN", "Guinea"),
    ("GNB", "Guinea-Bissau"),
    ("KEN", "Kenya"),
    ("LSO", "Lesotho"),
    ("LBR", "Liberia"),
    ("LBY", "Libya"),
    ("MDG", "Madagascar"),
    ("MWI", "Malawi"),
    ("MLI", "Mali"),
    ("MRT", "Mauritania"),
    ("MUS", "Mauritius"),                   # NOT in AFRICA_ADM0; per-country shape only
    ("MAR", "Morocco"),
    ("MOZ", "Mozambique"),
    ("NAM", "Namibia"),
    ("NER", "Niger"),
    ("NGA", "Nigeria"),
    ("RWA", "Rwanda"),
    ("STP", "São Tomé and Príncipe"),       # DBF has plain 'i'; Wikipedia spelling
    ("SEN", "Senegal"),
    ("SYC", "Seychelles"),                  # NOT in AFRICA_ADM0; per-country shape only
    ("SLE", "Sierra Leone"),
    ("SOM", "Somalia"),
    ("ZAF", "South Africa"),
    ("SSD", "South Sudan"),                 # DBF: "S. Sudan" -- expanded
    ("SDN", "Sudan"),
    ("TZA", "Tanzania"),
    ("TGO", "Togo"),
    ("TUN", "Tunisia"),
    ("UGA", "Uganda"),
    ("ZMB", "Zambia"),
    ("ZWE", "Zimbabwe"),
)

#: Frozenset of the 54 valid ISO3 codes; used by the Plan 02-04 click handler
#: to validate a clicked AFRICA_ADM0 polygon's ``iso_a3`` property BEFORE
#: writing to session_state -- this prevents the documented ESH/-99 leak
#: (see RESEARCH §"CRITICAL FINDING: 54 != 54").
ISO3_SET: frozenset[str] = frozenset(iso3 for iso3, _ in COUNTRIES)

#: Module-private O(1) lookup backing :func:`name_for`. Kept private so
#: callers depend only on the public functions and on :data:`COUNTRIES`.
_NAME_BY_ISO3: dict[str, str] = dict(COUNTRIES)


def iter_countries() -> list[tuple[str, str]]:
    """Return the ordered list of ``(ISO3, display name)`` pairs (D-29 API).

    Returns:
        A fresh ``list`` snapshot of :data:`COUNTRIES` -- callers may mutate
        the returned list without affecting the module-level tuple. Order is
        alphabetical-by-name with Angola first; this order IS the picker
        display order (D-25) and the first entry IS the first-load default
        (D-26).
    """
    return list(COUNTRIES)


def name_for(iso3: str) -> str:
    """Return the display name for an ISO3 code (D-29 API).

    Args:
        iso3: Three-letter ISO 3166 alpha-3 code (e.g. ``"AGO"``).

    Returns:
        The MOSAIC-conventional display name for the country, or the input
        ``iso3`` unchanged if the code is not known to this module. The
        fallback makes the helper safe to use as a ``format_func`` on a
        ``st.selectbox`` that might transiently hold a stale ISO3 (e.g.,
        during click-handler validation) -- there is no scenario in which
        this function raises.
    """
    return _NAME_BY_ISO3.get(iso3, iso3)


def warn_if_drifted_from_shapefiles(available_iso3s: Iterable[str]) -> None:
    """Emit a single warning if metadata diverges from shapefile presence (D-29).

    The expected divergence on Phase 1 / Phase 2 boundary data is:

    - In metadata but no shapefile: ``{}`` (none -- MUS and SYC have
      per-country shapes, so they appear in :func:`available_iso3s`).
    - In shapefiles but not metadata: ``{}`` (none -- ESH/-99 live only in
      AFRICA_ADM0.dbf, not in the per-country file enumeration).

    If MOSAIC-data upstream changes (a new ISO3 appears, an existing one is
    removed) the warning fires so the divergence is visible in the
    Streamlit launch logs. Per D-29 the function never raises; tolerating
    divergence preserves the D-04 spirit of "missing data degrades, doesn't
    crash".

    Args:
        available_iso3s: Output of
            :func:`mosaic_dashboard.data.shapefiles.available_countries`
            (or any iterable of ISO3 codes). Passed in by the caller so
            this module avoids a circular import on ``shapefiles``.

    Returns:
        ``None`` in all cases; the side effect is a single
        ``logging.warning`` line on divergence.
    """
    available = set(available_iso3s)
    meta = set(ISO3_SET)
    in_meta_not_shapes = meta - available
    in_shapes_not_meta = available - meta
    if in_meta_not_shapes or in_shapes_not_meta:
        log.warning(
            "Country metadata / shapefile drift detected: "
            "in metadata but no shapefile: %s; "
            "in shapefiles but not metadata: %s",
            sorted(in_meta_not_shapes),
            sorted(in_shapes_not_meta),
        )
