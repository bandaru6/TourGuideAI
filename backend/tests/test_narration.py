import pytest

from app.engine.narration import NarrationEngine
from app.models.trip import FunFact, Stop, StopType


def _stop(name: str = "Test Stop", description: str = "", fun_facts: list[FunFact] | None = None) -> Stop:
    return Stop(
        name=name,
        type=StopType.SCENIC,
        lat=34.0,
        lng=-118.0,
        description=description,
        suggested_duration_min=30,
        fun_facts=fun_facts or [],
    )


def test_approach_narration_format():
    """Approach narration should include distance and stop name."""
    engine = NarrationEngine()
    stop = _stop("Malibu Beach", description="A beautiful sandy beach on the Pacific Coast.")
    text = engine.approach_narration(stop, 2000)
    assert "Malibu Beach" in text
    assert "2.0 kilometers" in text
    assert "beautiful" in text.lower() or "sandy" in text.lower()
    assert "30 minutes" in text


def test_arrival_with_fun_fact():
    """Arrival narration should include fun fact if available."""
    engine = NarrationEngine()
    stop = _stop("Santa Monica Pier", fun_facts=[
        FunFact(text="The pier was built in 1909.")
    ])
    text = engine.arrival_narration(stop)
    assert "Santa Monica Pier" in text
    assert "1909" in text


def test_segment_transition_format():
    """Segment transition should include destination and time."""
    engine = NarrationEngine()
    text = engine.segment_transition("Stop A", "Stop B", 3600)
    assert "Stop B" in text
    assert "60 minutes" in text


def test_empty_description_approach():
    """Approach narration should handle empty description gracefully."""
    engine = NarrationEngine()
    stop = _stop("Mystery Stop", description="")
    text = engine.approach_narration(stop, 1500)
    assert "Mystery Stop" in text
    assert "scenic" in text.lower()  # Falls back to type label
