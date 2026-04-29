"""Shared county-name normalization for all niche directory sites.

Indiana counties are written with multiple variants in source data:
- IPLA emits "Saint Joseph", canonical is "St. Joseph"
- Some scrapers write "La Porte", canonical is "LaPorte"
- Same for "La Grange" → "LaGrange", "De Kalb" → "DeKalb"

Without normalization, the contractor template's slug builder produces
broken URLs like `/counties/saint-joseph-county/` that 404. This module
maps any known variant back to the canonical display name and slug.

Usage:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ipla-data'))
    from normalize_county import normalize_county, county_slug, city_to_county

    county = normalize_county(raw_county) or city_to_county(raw_city)
    slug = county_slug(county) if county else None
"""

from __future__ import annotations

import re
from pathlib import Path

# City → county lookup, generated from Census Bureau ANSI INCITS data.
# Re-run build_county_data.py to refresh.
_DATA_PATH = Path(__file__).parent
import sys as _sys
_sys.path.insert(0, str(_DATA_PATH))
from county_data import CITY_TO_COUNTY as _CENSUS_CITY_TO_COUNTY


# Canonical 92 Indiana counties. Each entry is (canonical_display, slug).
# Slug must match the filename of the corresponding county YAML in each site.
_CANONICAL_COUNTIES: list[tuple[str, str]] = [
    ("Adams", "adams-county"),
    ("Allen", "allen-county"),
    ("Bartholomew", "bartholomew-county"),
    ("Benton", "benton-county"),
    ("Blackford", "blackford-county"),
    ("Boone", "boone-county"),
    ("Brown", "brown-county"),
    ("Carroll", "carroll-county"),
    ("Cass", "cass-county"),
    ("Clark", "clark-county"),
    ("Clay", "clay-county"),
    ("Clinton", "clinton-county"),
    ("Crawford", "crawford-county"),
    ("Daviess", "daviess-county"),
    ("Dearborn", "dearborn-county"),
    ("Decatur", "decatur-county"),
    ("DeKalb", "dekalb-county"),
    ("Delaware", "delaware-county"),
    ("Dubois", "dubois-county"),
    ("Elkhart", "elkhart-county"),
    ("Fayette", "fayette-county"),
    ("Floyd", "floyd-county"),
    ("Fountain", "fountain-county"),
    ("Franklin", "franklin-county"),
    ("Fulton", "fulton-county"),
    ("Gibson", "gibson-county"),
    ("Grant", "grant-county"),
    ("Greene", "greene-county"),
    ("Hamilton", "hamilton-county"),
    ("Hancock", "hancock-county"),
    ("Harrison", "harrison-county"),
    ("Hendricks", "hendricks-county"),
    ("Henry", "henry-county"),
    ("Howard", "howard-county"),
    ("Huntington", "huntington-county"),
    ("Jackson", "jackson-county"),
    ("Jasper", "jasper-county"),
    ("Jay", "jay-county"),
    ("Jefferson", "jefferson-county"),
    ("Jennings", "jennings-county"),
    ("Johnson", "johnson-county"),
    ("Knox", "knox-county"),
    ("Kosciusko", "kosciusko-county"),
    ("LaGrange", "lagrange-county"),
    ("Lake", "lake-county"),
    ("LaPorte", "laporte-county"),
    ("Lawrence", "lawrence-county"),
    ("Madison", "madison-county"),
    ("Marion", "marion-county"),
    ("Marshall", "marshall-county"),
    ("Martin", "martin-county"),
    ("Miami", "miami-county"),
    ("Monroe", "monroe-county"),
    ("Montgomery", "montgomery-county"),
    ("Morgan", "morgan-county"),
    ("Newton", "newton-county"),
    ("Noble", "noble-county"),
    ("Ohio", "ohio-county"),
    ("Orange", "orange-county"),
    ("Owen", "owen-county"),
    ("Parke", "parke-county"),
    ("Perry", "perry-county"),
    ("Pike", "pike-county"),
    ("Porter", "porter-county"),
    ("Posey", "posey-county"),
    ("Pulaski", "pulaski-county"),
    ("Putnam", "putnam-county"),
    ("Randolph", "randolph-county"),
    ("Ripley", "ripley-county"),
    ("Rush", "rush-county"),
    ("Scott", "scott-county"),
    ("Shelby", "shelby-county"),
    ("Spencer", "spencer-county"),
    ("Starke", "starke-county"),
    ("Steuben", "steuben-county"),
    ("St. Joseph", "st-joseph-county"),
    ("Sullivan", "sullivan-county"),
    ("Switzerland", "switzerland-county"),
    ("Tippecanoe", "tippecanoe-county"),
    ("Tipton", "tipton-county"),
    ("Union", "union-county"),
    ("Vanderburgh", "vanderburgh-county"),
    ("Vermillion", "vermillion-county"),
    ("Vigo", "vigo-county"),
    ("Wabash", "wabash-county"),
    ("Warren", "warren-county"),
    ("Warrick", "warrick-county"),
    ("Washington", "washington-county"),
    ("Wayne", "wayne-county"),
    ("Wells", "wells-county"),
    ("White", "white-county"),
    ("Whitley", "whitley-county"),
]

# Variant spellings that map back to canonical. Keys are lowercase + whitespace-collapsed.
# Add new aliases here whenever an unrecognized variant shows up in source data.
_ALIASES: dict[str, str] = {
    # St. Joseph (IPLA writes "Saint Joseph"; some sources write "St Joseph" no period)
    "saint joseph": "St. Joseph",
    "st joseph": "St. Joseph",
    "st.joseph": "St. Joseph",
    "stjoseph": "St. Joseph",
    # LaPorte (Census uses "La Porte" for the city, "LaPorte" for the county)
    "la porte": "LaPorte",
    "laporte": "LaPorte",
    # LaGrange
    "la grange": "LaGrange",
    "lagrange": "LaGrange",
    # DeKalb
    "de kalb": "DeKalb",
    "dekalb": "DeKalb",
    # Vermilion vs Vermillion (IN uses two L's)
    "vermilion": "Vermillion",
}


def _key(value: str) -> str:
    """Normalize a string for case-insensitive, whitespace-tolerant lookup."""
    return re.sub(r"\s+", " ", value.strip()).lower()


# Build runtime lookup tables from canonical list + aliases.
_CANONICAL_BY_KEY: dict[str, str] = {}
_SLUG_BY_CANONICAL: dict[str, str] = {}
for _canonical, _slug in _CANONICAL_COUNTIES:
    _CANONICAL_BY_KEY[_key(_canonical)] = _canonical
    _SLUG_BY_CANONICAL[_canonical] = _slug
for _alias, _target in _ALIASES.items():
    _CANONICAL_BY_KEY[_key(_alias)] = _target


def normalize_county(value: str | None) -> str | None:
    """Return the canonical county name for any known variant.

    Returns None for empty input, "Unknown", or unrecognized values.
    The caller can then fall back to city_to_county() or skip the link.
    """
    if not value:
        return None
    cleaned = value.strip().rstrip(",.").strip()
    if not cleaned or cleaned.lower() == "unknown":
        return None
    # Strip trailing " County" if present
    cleaned = re.sub(r"\s+county\s*$", "", cleaned, flags=re.IGNORECASE).strip()
    return _CANONICAL_BY_KEY.get(_key(cleaned))


def county_slug(value: str | None) -> str | None:
    """Return the canonical URL slug for any known county variant.

    Returns None if the value can't be resolved. Callers should NOT render
    a link in that case (otherwise the link will 404).
    """
    canonical = normalize_county(value)
    return _SLUG_BY_CANONICAL.get(canonical) if canonical else None


def city_to_county(city: str | None) -> str | None:
    """Return the canonical county for a known Indiana city.

    Used as a fallback when source data omits or marks county as Unknown.
    Backed by the U.S. Census Bureau ANSI INCITS dataset (~695 IN places).
    """
    if not city:
        return None
    primary = _CENSUS_CITY_TO_COUNTY.get(city.strip())
    if primary:
        return normalize_county(primary)
    # Try title-case variant (handles ALL CAPS or lowercase input)
    primary = _CENSUS_CITY_TO_COUNTY.get(city.strip().title())
    return normalize_county(primary) if primary else None


def all_canonical_counties() -> list[tuple[str, str]]:
    """Expose the canonical (display, slug) list for build-time codegen."""
    return list(_CANONICAL_COUNTIES)


def all_aliases() -> dict[str, str]:
    """Expose the alias→canonical mapping for build-time codegen (TS export)."""
    return dict(_ALIASES)
