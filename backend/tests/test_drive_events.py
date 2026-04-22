import pytest
from app.engine.drive_events import DriveEventEngine
from app.models.corridor import CorridorGeometry, CorridorPoint
from app.models.drive_events import DriveEventType, TripState
from app.models.scoring import StopScore
from app.models.trip import Trip, Stop, StopType, FunFact
from app.models.preferences import UserPreferences

import polyline as polyline_lib


def _make_trip() -> Trip:
    path = [(37.0, -122.0), (36.5, -121.5), (36.0, -121.0)]
    encoded = polyline_lib.encode(path)

    return Trip(
        id="test-trip",
        origin="Start",
        destination="End",
        state=TripState.ACTIVE,
        route_polyline=encoded,
        corridor=CorridorGeometry(
            route_polyline=encoded,
            sample_points=[
                CorridorPoint(lat=37.0, lng=-122.0, distance_along_route_m=0, bearing=180),
                CorridorPoint(lat=36.5, lng=-121.5, distance_along_route_m=40_000, bearing=180),
                CorridorPoint(lat=36.0, lng=-121.0, distance_along_route_m=80_000, bearing=180),
            ],
            corridor_width_m=8000,
            total_distance_m=80_000,
        ),
        stops=[
            Stop(
                id="stop-1",
                name="Scenic Point",
                type=StopType.SCENIC,
                lat=36.5,
                lng=-121.5,
                distance_along_route_m=40_000,
                score=StopScore(
                    preference_match=0.5,
                    scenic_value=0.8,
                    meal_fit=0.0,
                    timing_fit=0.5,
                    detour_penalty=0.1,
                    total_score=0.5,
                    selection_reason="test",
                ),
                fun_facts=[
                    FunFact(
                        text="This area has amazing wildlife!",
                        trigger_lat=36.5,
                        trigger_lng=-121.5,
                        radius_m=3000,
                    )
                ],
            ),
        ],
    )


class TestDriveEventEngine:
    def test_approaching_stop(self):
        trip = _make_trip()
        engine = DriveEventEngine(trip)

        # Position 1.5km from the stop
        events = engine.process_location(36.51, -121.51)
        approach_events = [e for e in events if e.type == DriveEventType.APPROACHING_STOP]
        assert len(approach_events) == 1
        assert "Scenic Point" in approach_events[0].message

    def test_arrived_at_stop(self):
        trip = _make_trip()
        engine = DriveEventEngine(trip)

        # Position right at the stop
        events = engine.process_location(36.5, -121.5)
        entered = [e for e in events if e.type == DriveEventType.ENTERED_REGION]
        assert len(entered) == 1

    def test_no_duplicate_triggers(self):
        trip = _make_trip()
        engine = DriveEventEngine(trip)

        # Trigger approach
        engine.process_location(36.51, -121.51)
        # Same position again
        events = engine.process_location(36.51, -121.51)
        approach_events = [e for e in events if e.type == DriveEventType.APPROACHING_STOP]
        assert len(approach_events) == 0  # already triggered

    def test_fun_fact_trigger(self):
        trip = _make_trip()
        engine = DriveEventEngine(trip)

        events = engine.process_location(36.51, -121.51)
        narrations = [e for e in events if e.type == DriveEventType.NARRATION_TRIGGER]
        assert len(narrations) == 1
        assert "wildlife" in narrations[0].message

    def test_off_corridor_detection(self):
        trip = _make_trip()
        engine = DriveEventEngine(trip)

        # Far off corridor — trigger 3 times
        engine.process_location(37.0, -119.0)
        engine.process_location(37.0, -119.0)
        events = engine.process_location(37.0, -119.0)
        reroute = [e for e in events if e.type == DriveEventType.REROUTE_NEEDED]
        assert len(reroute) == 1
