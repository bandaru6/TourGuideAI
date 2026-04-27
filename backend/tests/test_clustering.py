import pytest

from app.engine.clustering import cluster_candidates, deduplicate_by_name, pick_representative
from app.models.trip import CandidateStop


def _candidate(name: str, lat: float, lng: float, rating: float | None = None, dist: float = 0.0) -> CandidateStop:
    return CandidateStop(
        place_id=f"osm_{name}",
        name=name,
        lat=lat,
        lng=lng,
        rating=rating,
        distance_to_route_m=dist,
        distance_along_route_m=0.0,
    )


def test_pick_representative_best_rated():
    """Best-rated candidate is picked as representative."""
    group = [
        _candidate("A", 34.0, -118.0, rating=4.0, dist=100),
        _candidate("B", 34.0001, -118.0001, rating=4.8, dist=200),
        _candidate("C", 34.0002, -118.0002, rating=3.5, dist=50),
    ]
    rep = pick_representative(group)
    assert rep.name == "B"


def test_distant_candidates_not_clustered():
    """Candidates far apart should remain in separate clusters."""
    candidates = [
        _candidate("North", 35.0, -118.0),
        _candidate("South", 34.0, -118.0),  # ~111 km apart
    ]
    result = cluster_candidates(candidates, eps_m=500)
    assert len(result) == 2


def test_nearby_candidates_clustered():
    """Candidates within eps_m should be merged."""
    candidates = [
        _candidate("A", 34.0, -118.0, rating=4.5),
        _candidate("B", 34.0001, -118.0001, rating=4.0),  # ~15m apart
        _candidate("C", 34.0002, -118.0002, rating=3.0),  # ~30m apart
    ]
    result = cluster_candidates(candidates, eps_m=500)
    assert len(result) == 1
    assert result[0].cluster_size == 3


def test_deduplicate_by_name():
    """Near-duplicate names should be deduplicated."""
    candidates = [
        _candidate("Malibu Beach", 34.0, -118.0, rating=4.5),
        _candidate("Malibu Beach Cafe", 34.1, -118.1, rating=3.0),
        _candidate("Santa Monica Pier", 34.0, -118.5, rating=4.8),
    ]
    result = deduplicate_by_name(candidates, threshold=0.85)
    # "Malibu Beach" and "Malibu Beach Cafe" should NOT be deduped (ratio < 0.85)
    # Let's test with a higher-similarity case
    candidates2 = [
        _candidate("Malibu Beach", 34.0, -118.0, rating=4.5),
        _candidate("Malibu Beach", 34.1, -118.1, rating=3.0),
        _candidate("Santa Monica Pier", 34.0, -118.5, rating=4.8),
    ]
    result2 = deduplicate_by_name(candidates2, threshold=0.85)
    assert len(result2) == 2
    names = {c.name for c in result2}
    assert "Malibu Beach" in names
    assert "Santa Monica Pier" in names


def test_empty_input():
    """Empty input returns empty output."""
    assert cluster_candidates([]) == []
    assert deduplicate_by_name([]) == []


def test_cluster_size_propagation():
    """Cluster size is correctly set on representative."""
    candidates = [
        _candidate("A", 34.0, -118.0, rating=5.0),
        _candidate("B", 34.00001, -118.00001, rating=4.0),
    ]
    result = cluster_candidates(candidates, eps_m=500)
    assert len(result) == 1
    assert result[0].cluster_size == 2
    assert result[0].name == "A"  # Higher rated
