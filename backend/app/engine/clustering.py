"""
Spatial clustering & deduplication for candidate stops.

Uses grid-based spatial clustering (no scikit-learn dependency).
Quantizes lat/lng into cells of configurable size, then picks the
best representative per cluster.
"""

from difflib import SequenceMatcher

from app.models.trip import CandidateStop

# Earth circumference ≈ 40,075 km → 1 degree lat ≈ 111,320 m
METERS_PER_DEG_LAT = 111_320


def _cell_key(lat: float, lng: float, cell_size_deg: float) -> tuple[int, int]:
    return (int(lat / cell_size_deg), int(lng / cell_size_deg))


def cluster_candidates(
    candidates: list[CandidateStop], eps_m: float = 500
) -> list[CandidateStop]:
    """
    Grid-based spatial clustering. Candidates within the same grid cell
    (of side length eps_m) are grouped together. The best representative
    is picked per group.
    """
    if not candidates:
        return []

    cell_size_deg = eps_m / METERS_PER_DEG_LAT

    groups: dict[tuple[int, int], list[CandidateStop]] = {}
    for c in candidates:
        key = _cell_key(c.lat, c.lng, cell_size_deg)
        groups.setdefault(key, []).append(c)

    result: list[CandidateStop] = []
    for group in groups.values():
        rep = pick_representative(group)
        rep.cluster_size = len(group)
        result.append(rep)

    return result


def pick_representative(group: list[CandidateStop]) -> CandidateStop:
    """Pick the best candidate from a cluster: highest rating, then closest to route."""
    if len(group) == 1:
        return group[0]

    def sort_key(c: CandidateStop) -> tuple[float, float]:
        rating = c.rating if c.rating is not None else 0.0
        return (-rating, c.distance_to_route_m)

    return sorted(group, key=sort_key)[0]


def deduplicate_by_name(
    candidates: list[CandidateStop], threshold: float = 0.85
) -> list[CandidateStop]:
    """Remove near-duplicate candidates by name similarity."""
    if not candidates:
        return []

    kept: list[CandidateStop] = []
    for c in candidates:
        is_dup = False
        for existing in kept:
            ratio = SequenceMatcher(
                None, c.name.lower(), existing.name.lower()
            ).ratio()
            if ratio >= threshold:
                # Keep the one with better rating
                if (c.rating or 0) > (existing.rating or 0):
                    kept.remove(existing)
                    kept.append(c)
                is_dup = True
                break
        if not is_dup:
            kept.append(c)

    return kept
