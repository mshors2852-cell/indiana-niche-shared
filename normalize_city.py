"""
Shared city-name normalization for all niche directory refresh scripts.

Indiana has several towns whose names are commonly written with both "Saint X"
and "St. X" variants in source data (IPLA CSVs, Google Places, etc). The
inconsistency causes URL slug splits like /cities/saint-john/ and /cities/st-john/
which fragments SEO and creates 404s on cross-site links.

Canonical form: "St. X" (period + space). Slugifies to /cities/st-x/.

Usage:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ipla-data'))
    from normalize_city import normalize_city

    city = normalize_city(raw_city_value)
"""

import re

# Map of canonical forms to their accepted variant patterns (case-insensitive).
# Each pattern is matched against the entire (stripped) city value.
SAINT_CANONICAL = {
    "St. John":     [r"saint\s*john",        r"st\.?\s*john"],
    "St. Anthony":  [r"saint\s*anthony",     r"st\.?\s*anthony"],
    "St. Joe":      [r"saint\s*joe(?!ph)",   r"st\.?\s*joe(?!ph)"],
    "St. Joseph":   [r"saint\s*joseph",      r"st\.?\s*joseph"],
    "St. Leon":     [r"saint\s*leon",        r"st\.?\s*leon"],
    "St. Meinrad":  [r"saint\s*meinrad",     r"st\.?\s*meinrad"],
}

_COMPILED = []
for canonical, patterns in SAINT_CANONICAL.items():
    for pat in patterns:
        _COMPILED.append((re.compile(rf"^{pat}$", re.IGNORECASE), canonical))


def normalize_city(value: str) -> str:
    """Return the canonical form if value matches a known Saint variant.

    Returns the input unchanged for any city not in the known list.
    Strips surrounding whitespace before matching.
    """
    if not value:
        return value
    stripped = str(value).strip()
    for regex, canonical in _COMPILED:
        if regex.match(stripped):
            return canonical
    return value
