import pytest
from app.engine.ranking import score_candidate, rank_candidates, generate_selection_reason
from app.models.corridor import CorridorGeometry, CorridorPoint
from app.models.preferences import UserPreferences
from app.models.scoring import RankingWeights
from app.models.trip import CandidateStop


def _make_corridor(total_distance: float = 500_000, width: float = 8000) -> CorridorGeometry:
    return CorridorGeometry(
        route_polyline="",
        sample_points=[
            CorridorPoint(lat=37.0, lng=-122.0, distance_along_route_m=0, bearing=180),
            CorridorPoint(lat=36.0, lng=-121.5, distance_along_route_m=250_000, bearing=180),
            CorridorPoint(lat=35.0, lng=-121.0, distance_along_route_m=500_000, bearing=180),
        ],
        corridor_width_m=width,
        total_distance_m=total_distance,
    )


def _make_candidate(
    name: str = "Test Place",
    types: list[str] | None = None,
    rating: float = 4.0,
    distance_to_route: float = 1000,
    distance_along_route: float = 200_000,
) -> CandidateStop:
    return CandidateStop(
        place_id=f"place_{name.replace(' ', '_')}",
        name=name,
        lat=36.5,
        lng=-121.5,
        types=types or ["tourist_attraction"],
        rating=rating,
        distance_to_route_m=distance_to_route,
        distance_along_route_m=distance_along_route,
    )


class TestScoreCandidate:
    def test_basic_scoring(self):
        corridor = _make_corridor()
        prefs = UserPreferences(interests=["scenic", "beach"])
        candidate = _make_candidate(types=["beach", "natural_feature"], rating=4.7)

        score = score_candidate(candidate, prefs, corridor)
        assert 0 < score.total_score <= 1.0
        assert score.preference_match > 0
        assert score.scenic_value > 0
        assert score.selection_reason != ""

    def test_avoided_type_scores_zero(self):
        corridor = _make_corridor()
        prefs = UserPreferences(interests=["scenic"], avoid_types=["restaurant"])
        candidate = _make_candidate(types=["restaurant"], rating=4.5)

        score = score_candidate(candidate, prefs, corridor)
        assert score.preference_match == 0.0

    def test_high_detour_penalty(self):
        corridor = _make_corridor(width=8000)
        prefs = UserPreferences()
        close = _make_candidate(name="Close", distance_to_route=500)
        far = _make_candidate(name="Far", distance_to_route=7500)

        close_score = score_candidate(close, prefs, corridor)
        far_score = score_candidate(far, prefs, corridor)
        assert close_score.detour_penalty < far_score.detour_penalty

    def test_restaurant_meal_fit(self):
        corridor = _make_corridor()
        prefs = UserPreferences()
        restaurant = _make_candidate(
            name="Good Restaurant",
            types=["restaurant"],
            distance_along_route=165_000,  # ~1/3 of route
        )

        score = score_candidate(restaurant, prefs, corridor)
        assert score.meal_fit > 0.5


class TestRankCandidates:
    def test_ranking_order(self):
        corridor = _make_corridor()
        prefs = UserPreferences(interests=["beach"])

        candidates = [
            _make_candidate(name="Gas Station", types=["gas_station"], rating=3.0),
            _make_candidate(name="Beautiful Beach", types=["beach", "natural_feature"], rating=4.8),
            _make_candidate(name="Random Shop", types=["store"], rating=3.5),
        ]

        ranked = rank_candidates(candidates, prefs, corridor)
        assert ranked[0][0].name == "Beautiful Beach"

    def test_empty_candidates(self):
        corridor = _make_corridor()
        prefs = UserPreferences()
        ranked = rank_candidates([], prefs, corridor)
        assert ranked == []


class TestGenerateSelectionReason:
    def test_reason_includes_name(self):
        candidate = _make_candidate(name="Sunset Beach")
        reason = generate_selection_reason(candidate, 0.8, 0.7, 0.0, 0.5, 0.9)
        assert "Sunset Beach" in reason

    def test_reason_mentions_interests(self):
        candidate = _make_candidate(name="Test")
        reason = generate_selection_reason(candidate, 0.8, 0.3, 0.0, 0.5, 0.5)
        assert "interests" in reason.lower() or "matches" in reason.lower()
