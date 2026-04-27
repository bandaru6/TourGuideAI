import pytest

from app.engine.traffic import estimate_congestion, adjust_segment_duration, suggest_drops, apply_traffic_to_segments
from app.models.trip import Segment, Stop, StopType
from app.models.scoring import StopScore


def _stop(name: str, score: float, duration: int = 30) -> Stop:
    return Stop(
        name=name,
        type=StopType.SCENIC,
        lat=34.0,
        lng=-118.0,
        suggested_duration_min=duration,
        score=StopScore(
            preference_match=0.5,
            scenic_value=0.5,
            meal_fit=0.0,
            timing_fit=0.5,
            detour_penalty=0.0,
            total_score=score,
            selection_reason=f"{name}: test",
        ),
    )


def test_rush_hour_congestion():
    """Weekday rush hours should have high congestion."""
    morning = estimate_congestion(34.0, -118.0, 8.0, 1)  # Tuesday 8 AM
    evening = estimate_congestion(34.0, -118.0, 17.0, 3)  # Thursday 5 PM
    assert morning >= 0.7
    assert evening >= 0.8


def test_midnight_low_congestion():
    """Late night should have very low congestion."""
    midnight = estimate_congestion(34.0, -118.0, 2.0, 1)
    assert midnight <= 0.1


def test_adjustment_math():
    """Duration adjustment should follow the formula: base * (1 + congestion * 0.8)."""
    result = adjust_segment_duration(1000.0, 0.5)
    expected = 1000.0 * (1 + 0.5 * 0.8)
    assert abs(result - expected) < 0.01


def test_drop_ordering():
    """Lowest-scored stops should be dropped first."""
    stops = [
        _stop("High", 0.8, 30),
        _stop("Low", 0.2, 30),
        _stop("Mid", 0.5, 30),
    ]
    drops = suggest_drops(stops, behind_schedule_s=1800)  # 30 min behind
    assert drops[0].name == "Low"


def test_no_drops_when_on_time():
    """No drops when not behind schedule."""
    stops = [_stop("A", 0.5, 30)]
    drops = suggest_drops(stops, behind_schedule_s=0)
    assert len(drops) == 0
