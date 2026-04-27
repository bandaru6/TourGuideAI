import pytest

from app.engine.constraint_solver import ConstraintSolver, _parse_opening_hours
from app.engine.itinerary import build_itinerary
from app.models.corridor import CorridorGeometry, CorridorPoint
from app.models.preferences import UserPreferences
from app.models.scoring import StopScore
from app.models.trip import CandidateStop


def _corridor(total_distance_m: float = 500_000) -> CorridorGeometry:
    return CorridorGeometry(
        route_polyline="",
        sample_points=[
            CorridorPoint(lat=34.0, lng=-118.0, distance_along_route_m=0, bearing=0),
            CorridorPoint(lat=35.0, lng=-117.0, distance_along_route_m=total_distance_m, bearing=0),
        ],
        corridor_width_m=10000,
        total_distance_m=total_distance_m,
    )


def _candidate(name: str, along_m: float, rating: float = 4.0, types: list[str] | None = None, opening_hours: str | None = None) -> CandidateStop:
    return CandidateStop(
        place_id=f"osm_{name}",
        name=name,
        lat=34.5,
        lng=-117.5,
        types=types or ["tourist_attraction", "point_of_interest"],
        rating=rating,
        distance_to_route_m=500,
        distance_along_route_m=along_m,
        opening_hours=opening_hours,
    )


def _score(total: float = 0.5) -> StopScore:
    return StopScore(
        preference_match=0.5,
        scenic_value=0.5,
        meal_fit=0.0,
        timing_fit=0.5,
        detour_penalty=0.1,
        total_score=total,
        selection_reason="test",
    )


def test_time_window_filtering():
    """Stops with incompatible time windows should be excluded."""
    corridor = _corridor()
    # This stop opens at 14:00 but we arrive around 10:00 (early in route)
    candidates = [
        (_candidate("Early Stop", 50_000, opening_hours="14:00-20:00"), _score(0.8)),
        (_candidate("Open Stop", 50_000, opening_hours="06:00-22:00"), _score(0.6)),
    ]
    solver = ConstraintSolver(
        candidates, corridor, UserPreferences(),
        base_duration_s=18000, departure_hour=9.0,
    )
    stops = solver.solve()
    names = [s.name for s in stops]
    assert "Open Stop" in names
    # Early Stop should be excluded due to time window
    assert "Early Stop" not in names


def test_ev_charging_insertion():
    """EV charging stops should be inserted when range is exceeded."""
    corridor = _corridor(total_distance_m=600_000)
    prefs = UserPreferences(vehicle_range_km=300)
    candidates = [
        (_candidate("Stop A", 100_000), _score(0.7)),
        (_candidate("Stop B", 500_000), _score(0.6)),
    ]
    charging = [
        _candidate("Charger", 300_000, types=["charging_station"]),
    ]
    solver = ConstraintSolver(
        candidates, corridor, prefs,
        base_duration_s=21600,
        charging_candidates=charging,
    )
    stops = solver.solve()
    names = [s.name for s in stops]
    assert "Charger" in names


def test_per_stop_detour_limit():
    """Stops exceeding per-stop detour limit should be excluded."""
    corridor = _corridor()
    prefs = UserPreferences(max_detour_per_stop_min=5)  # 5 min at ~28 m/s ≈ 8333m
    far = CandidateStop(
        place_id="far",
        name="Far Stop",
        lat=34.5, lng=-117.5,
        types=["tourist_attraction"],
        rating=4.5,
        distance_to_route_m=50_000,  # 50 km off route
        distance_along_route_m=200_000,
    )
    close = CandidateStop(
        place_id="close",
        name="Close Stop",
        lat=34.5, lng=-117.5,
        types=["tourist_attraction"],
        rating=4.0,
        distance_to_route_m=1_000,
        distance_along_route_m=200_000,
    )
    solver = ConstraintSolver(
        [(far, _score(0.9)), (close, _score(0.5))],
        corridor, prefs, base_duration_s=21600,
    )
    stops = solver.solve()
    names = [s.name for s in stops]
    assert "Close Stop" in names
    assert "Far Stop" not in names


def test_fallback_to_greedy():
    """Empty solver result should allow fallback to greedy."""
    corridor = _corridor()
    solver = ConstraintSolver([], corridor, UserPreferences())
    stops = solver.solve()
    assert stops == []
    # Greedy also returns empty for no candidates
    greedy = build_itinerary([], corridor, UserPreferences())
    assert greedy == []


def test_beam_finds_better_solution():
    """Beam search should find at least as good a solution as greedy."""
    corridor = _corridor()
    candidates = [
        (_candidate(f"Stop_{i}", i * 80_000), _score(0.5 + i * 0.05))
        for i in range(1, 6)
    ]
    solver = ConstraintSolver(candidates, corridor, UserPreferences(), base_duration_s=21600)
    beam_stops = solver.solve(beam_width=10)
    greedy_stops = build_itinerary(candidates, corridor, UserPreferences(), base_duration_s=21600)
    assert len(beam_stops) >= len(greedy_stops)


def test_backward_compat_no_opening_hours():
    """Candidates without opening hours should be accepted."""
    corridor = _corridor()
    candidates = [
        (_candidate("No Hours", 200_000), _score(0.7)),
    ]
    solver = ConstraintSolver(candidates, corridor, UserPreferences(), base_duration_s=21600)
    stops = solver.solve()
    assert len(stops) >= 1
    assert stops[0].name == "No Hours"
