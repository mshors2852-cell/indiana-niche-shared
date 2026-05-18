"""Shared helper: query Command Center for contacts marked 'lost' on a site.

Used by discover/seed scripts across the directory cluster to avoid re-importing
businesses that previously requested removal (`pipeline_stage='lost'` in CC).

Without this guard, deleting a contractor's YAML at owner request would just
re-import them on the next discovery run — the existing per-script exclusion
logic only checks YAMLs currently on disk, not historical CC state.

Usage in a discovery script::

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ipla-data'))
    from cc_exclusions import load_excluded_signals

    excluded_place_ids, excluded_slugs = load_excluded_signals("inmoldpros")
    # ...then in the main discovery loop:
    if place_id in excluded_place_ids or generated_slug in excluded_slugs:
        continue
"""

import subprocess
import sys

VPS_TARGET = "root@100.76.9.107"
VPS_TIMEOUT = 10  # seconds


def load_excluded_signals(site_slug: str) -> tuple[set[str], set[str]]:
    """Query CC for googlePlaceIds + slugs of contacts marked lost on this site.

    Runs over SSH to the dev VPS — assumes Tailscale is connected. If the
    VPS is unreachable, returns empty sets and logs a WARNING rather than
    failing the calling script. Discovery runs should still proceed; the
    operator will see the warning and can review new YAMLs before deploying.

    Args:
        site_slug: The CC ``sites.slug`` value to filter on (e.g.,
            ``"inmoldpros"``, ``"indianafishing"``, ``"wisconsinfishing"``).

    Returns:
        ``(excluded_place_ids, excluded_slugs)`` — either may be empty.
        Discover scripts should skip a Google Places result if its place_id
        OR generated slug matches either set.
    """
    query = (
        f"SELECT COALESCE(google_place_id, ''), COALESCE(slug, '') "
        f"FROM contacts "
        f"WHERE site_slug = '{site_slug}' AND pipeline_stage = 'lost';"
    )
    try:
        result = subprocess.run(
            ["ssh", VPS_TARGET,
             f"sudo -u postgres psql command_center -tA -F'|' -c \"{query}\""],
            capture_output=True, text=True, timeout=VPS_TIMEOUT,
        )
        if result.returncode != 0:
            print(
                f"WARN: CC exclusion query failed for site={site_slug} "
                f"(rc={result.returncode}): {result.stderr.strip()}",
                file=sys.stderr,
            )
            print(
                "WARN: proceeding without lost-contact exclusion — review new YAMLs carefully",
                file=sys.stderr,
            )
            return set(), set()
    except Exception as e:
        print(
            f"WARN: CC exclusion query exception for site={site_slug}: {e}",
            file=sys.stderr,
        )
        print(
            "WARN: proceeding without lost-contact exclusion — review new YAMLs carefully",
            file=sys.stderr,
        )
        return set(), set()

    place_ids: set[str] = set()
    slugs: set[str] = set()
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 1)
        pid = parts[0].strip() if len(parts) >= 1 else ""
        sl = parts[1].strip() if len(parts) >= 2 else ""
        if pid:
            place_ids.add(pid)
        if sl:
            slugs.add(sl)
    return place_ids, slugs
