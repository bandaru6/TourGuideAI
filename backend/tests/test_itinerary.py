import pytest
from app.engine.itinerary import build_itinerary, _infer_stop_type
from app.engine.ranking import score_candidate
from app.models.corridor import CorridorGeometry, CorridorPoint
from app.models.preferences import UserPreferences
from app.models.scoring import StopScore, RankingWeights
from app.models.trip import CandidateStop, StopType


def _make_corridor(total_distance: float = 600_000) -> CorridorGeometry:
    return CorridorGeometry(
        route_polyline="",
        sample_points=[
            CorridorPoint(lat=37.7, lng=-122.4, distance_along_route_m=0, bearing=180),
            CorridorPoint(lat=36.5, lng=-121.5, distance_along_route_m=200_000, bearing=180),
            CorridorPoint(lat=35.5, lng=-120.5, distance_along_route_m=400_000, bearing=180),
            CorridorPoint(lat=34.0, lng=-118.2, distance_along_route_m=600_000, bearing=180),
        ],
        corridor_width_m=8000,
        total_distance_m=total_distance,
    )


def _make_scored_candidate(
    name: str,
    types: list[str],
    distance_along: float,
    score_total: float = 0.5,
) -> tuple[CandidateStop, StopScore]:
    candidate = CandidateStop(
        place_id=f"place_{name.replace(' ', '_')}",
        name=name,
        lat=36.0,
        lng=-121.0,
        types=types,
        rating=4.0,
        distance_to_route_m=1000,
        distance_along_route_m=distance_along,
    )
    score = StopScore(
        preference_match=0.5,
        scenic_value=0.5,
        meal_fit=0.5 if "restaurant" in types else 0.0,
        timing_fit=0.5,
        detour_penalty=0.1,
        total_score=score_total,
        selection_reason=f"{name}: test reason",
    )
    return candidate, score


class TestBuildItinerary:
    def test_basic_itinerary(self):
        corridor = _make_corridor()
        prefs = UserPreferences(stop_interval_min=60, stop_interval_max=180)

        ranked = [
            _make_scored_candidate("Beach A", ["beach"], 100_000, 0.8),
            _make_scored_candidate("Restaurant", ["restaurant"], 200_000, 0.7),
            _make_scored_candidate("Park", ["park"], 350_000, 0.6),
            _make_scored_candidate("Museum", ["museum"], 500_000, 0.5),
        ]

        stops = build_itinerary(ranked, corridor, prefs, base_duration_s=21600)
        assert len(stops) > 0
        # Stops should be ordered by distance along route
        distances = [s.distance_along_route_m for s in stops]
        assert distances == sorted(distances)

    def test_empty_candidates(self):
        corridor = _make_corridor()
        prefs = UserPreferences()
        stops = build_itinerary([], corridor, prefs)
        assert stops == []

    def test_stop_spacing(self):
        corridor = _make_corridor(600_000)
        prefs = UserPreferences(stop_interval_min=60, stop_interval_max=180)

        # Create candidates spaced along route
        ranked = [
            _make_scored_candidate("Stop A", ["tourist_attraction"], 50_000, 0.8),
            _make_scored_candidate("Stop B", ["tourist_attraction"], 55_000, 0.7),  # too close to A
            _make_scored_candidate("Stop C", ["tourist_attraction"], 250_000, 0.6),
            _make_scored_candidate("Stop D", ["tourist_attraction"], 450_000, 0.5),
        ]

        stops = build_itinerary(ranked, corridor, prefs, base_duration_s=21600)
        # Stop B should be skipped (too close to A)
        names = [s.name for s in stops]
        if "Stop A" in names and "Stop B" in names:
            pytest.fail("Stop B should be skipped — too close to Stop A")

    def test_includes_meal_stop(self):
        corridor = _make_corridor(600_000)
        prefs = UserPreferences(stop_interval_min=60, stop_interval_max=180)

        ranked = [
            _make_scored_candidate("Viewpoint", ["point_of_interest"], 100_000, 0.9),
            _make_scored_candidate("Lunch Spot", ["restaurant"], 250_000, 0.6),
            _make_scored_candidate("Another View", ["point_of_interest"], 400_000, 0.7),
        ]

        stops = build_itinerary(ranked, corridor, prefs, base_duration_s=21600)
        types = [s.type for s in stops]
        assert StopType.RESTAURANT in types or StopType.CAFE in types


class TestInferStopType:
    def test_beach(self):
        assert _infer_stop_type(["beach", "point_of_interest"]) == StopType.BEACH

    def test_restaurant(self):
        assert _infer_stop_type(["restaurant", "food"]) == StopType.RESTAURANT

    def test_museum(self):
        assert _infer_stop_type(["museum"]) == StopType.MUSEUM

    def test_unknown(self):
        assert _infer_stop_type(["some_random_type"]) == StopType.OTHER
