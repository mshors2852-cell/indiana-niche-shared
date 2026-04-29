"""Tests for shared county normalization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from normalize_county import (
    normalize_county,
    county_slug,
    city_to_county,
    all_canonical_counties,
)


def test_canonical_counties_count():
    """All 92 IN counties present."""
    assert len(all_canonical_counties()) == 92


def test_normalize_passthrough():
    assert normalize_county("Marion") == "Marion"
    assert normalize_county("St. Joseph") == "St. Joseph"
    assert normalize_county("LaPorte") == "LaPorte"
    assert normalize_county("DeKalb") == "DeKalb"


def test_normalize_aliases():
    """The known IPLA / scraper variants all collapse to canonical."""
    assert normalize_county("Saint Joseph") == "St. Joseph"
    assert normalize_county("St Joseph") == "St. Joseph"
    assert normalize_county("La Porte") == "LaPorte"
    assert normalize_county("Laporte") == "LaPorte"
    assert normalize_county("La Grange") == "LaGrange"
    assert normalize_county("Lagrange") == "LaGrange"
    assert normalize_county("De Kalb") == "DeKalb"
    assert normalize_county("Dekalb") == "DeKalb"


def test_normalize_case_insensitive():
    assert normalize_county("saint joseph") == "St. Joseph"
    assert normalize_county("SAINT JOSEPH") == "St. Joseph"
    assert normalize_county("MARION") == "Marion"


def test_normalize_strips_county_suffix():
    """Inputs like 'St. Joseph County' should still resolve."""
    assert normalize_county("St. Joseph County") == "St. Joseph"
    assert normalize_county("Marion County") == "Marion"
    assert normalize_county("Saint Joseph County") == "St. Joseph"


def test_normalize_whitespace():
    assert normalize_county("  Saint Joseph  ") == "St. Joseph"
    assert normalize_county("Saint  Joseph") == "St. Joseph"


def test_normalize_empty_and_unknown():
    """Empty / Unknown / garbage inputs return None — caller MUST check."""
    assert normalize_county("") is None
    assert normalize_county(None) is None
    assert normalize_county("Unknown") is None
    assert normalize_county("UNKNOWN") is None
    assert normalize_county("   ") is None
    assert normalize_county("Nonexistent County") is None


def test_county_slug_canonical():
    assert county_slug("St. Joseph") == "st-joseph-county"
    assert county_slug("LaPorte") == "laporte-county"
    assert county_slug("LaGrange") == "lagrange-county"
    assert county_slug("DeKalb") == "dekalb-county"
    assert county_slug("Marion") == "marion-county"


def test_county_slug_aliases():
    """All variants resolve to the same canonical slug."""
    assert county_slug("Saint Joseph") == "st-joseph-county"
    assert county_slug("La Porte") == "laporte-county"
    assert county_slug("La Grange") == "lagrange-county"
    assert county_slug("De Kalb") == "dekalb-county"


def test_county_slug_returns_none_for_unknown():
    """Unknown county MUST return None so caller skips the link."""
    assert county_slug("") is None
    assert county_slug(None) is None
    assert county_slug("Unknown") is None
    assert county_slug("Notarealcounty") is None


def test_city_to_county_known():
    """Census-derived city lookup catches the cases that bit us."""
    # Fowler — the inplumberpros 404
    assert city_to_county("Fowler") == "Benton"
    # St. Joseph county cities
    assert city_to_county("South Bend") == "St. Joseph"
    assert city_to_county("Mishawaka") == "St. Joseph"
    # LaPorte county cities
    assert city_to_county("La Porte") == "LaPorte"
    assert city_to_county("Michigan City") == "LaPorte"
    # Top metros
    assert city_to_county("Indianapolis") == "Marion"
    assert city_to_county("Carmel") == "Hamilton"
    assert city_to_county("Fort Wayne") == "Allen"


def test_city_to_county_case_tolerant():
    assert city_to_county("INDIANAPOLIS") == "Marion"
    assert city_to_county("indianapolis") == "Marion"
    assert city_to_county("  fort wayne  ") == "Allen"


def test_city_to_county_unknown_returns_none():
    assert city_to_county("") is None
    assert city_to_county(None) is None
    assert city_to_county("Bogusville") is None


def test_every_canonical_has_unique_slug():
    """Sanity: no two counties share a slug."""
    slugs = [slug for _, slug in all_canonical_counties()]
    assert len(slugs) == len(set(slugs))


def test_no_canonical_resolves_to_broken_slug():
    """Every canonical county name → its declared slug, no naive fallback."""
    for name, slug in all_canonical_counties():
        assert county_slug(name) == slug, f"{name} should slug to {slug}"
