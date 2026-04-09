# indiana-niche-shared

Shared Python helpers for the M. Shores Tech Indiana niche directory cluster.

This directory lives at `~/sites/ipla-data/` on local machines (the original
name reflects its earlier role as the staging area for IPLA bulk CSV downloads).
The CSVs and PDFs are still kept here locally as the source data for refresh
scripts, but they are intentionally **not** versioned — only the shared Python
helpers are.

## What's in this repo

| File | Purpose |
|------|---------|
| `normalize_city.py` | Canonicalizes Indiana "Saint X" / "St X" / "St.X" city name variants to the canonical "St. X" form so all niche site URL slugs become `/cities/st-x/`. |

## How niche site refresh scripts use this

Each niche site's `refresh_*.py` script imports the shared helper using a
relative path that walks up two directories and into `ipla-data`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ipla-data'))
from normalize_city import normalize_city
```

This pattern assumes the niche sites and `ipla-data` sit as siblings under
`~/sites/`:

```
~/sites/
├── ipla-data/                 ← this repo
│   ├── normalize_city.py
│   └── (CSVs, PDFs — not versioned)
├── inappraiserpros/
├── inhomeinspectionpros/
├── inmoldpros/
├── inplumberpros/
├── inradonpros/
├── inwelldrillers/
└── indianaenvironmental/
```

If you clone this repo to a different location, update the import path in the
refresh scripts accordingly.

## Active consumers

As of 2026-04-09, these refresh scripts import from this module:

- `inappraiserpros/scripts/refresh_appraisers.py`
- `inhomeinspectionpros/scripts/refresh_inspectors.py`
- `inmoldpros/scripts/refresh_contractors.py`
- `inplumberpros/scripts/refresh_contractors.py`
- `inradonpros/scripts/refresh_contractors.py`
- `inwelldrillers/scripts/refresh_contractors.py`
- `indianaenvironmental/scripts/refresh_contractors.py`

If you add a new helper here, update this list.

## Adding a new helper

1. Drop the new module file in this directory.
2. Update each consuming refresh script with the import.
3. Update the README's "What's in this repo" table.
4. Commit + push.

## Why these helpers live in their own repo

The 7 niche directory sites are separate Astro projects with their own git
repos. Anything that needs to be **identical** across all of them — like
the canonical mapping of "Saint John" → "St. John" — should live in one
place to avoid drift. Inlining duplicate copies in 7 refresh scripts has
already caused real production bugs (e.g. `/cities/saint-john/` vs
`/cities/st-john/` slug splits prior to 2026-04-09).

Future candidates for migration into this repo:
- The `CITY_TO_COUNTY` mapping (currently duplicated in every refresh script)
- The `find_field` IPLA CSV column-variation helper
- A `slugify` helper consistent with Astro's URL generation
- A `phone_format` helper
