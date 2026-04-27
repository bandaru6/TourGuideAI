import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.corridor import CorridorGeometry, CorridorPoint
from app.models.preferences import UserPreferences
from app.models.scoring import StopScore
from app.models.trip import CandidateStop, Stop, Segment, Trip, StopType
from app.models.drive_events import TripState
from app.services.reroute_service import RerouteService


def _trip() -> Trip:
    return Trip(
        origin="San Francisco, CA",
        destination="Los Angeles, CA",
        preferences=UserPreferences(interests=["scenic"]),
        state=TripState.ACTIVE,
        stops=[
            Stop(
                id="stop1", name="Stop 1", type=StopType.SCENIC,
                lat=35.0, lng=-118.5,
                distance_along_route_m=200_000,
                score=StopScore(
                    preference_match=0.5, scenic_value=0.5, meal_fit=0.0,
                    timing_fit=0.5, detour_penalty=0.0, total_score=0.5,
                    selection_reason="test",
                ),
            ),
            Stop(
                id="stop2", name="Stop 2", type=StopType.RESTAURANT,
                lat=34.5, lng=-118.2,
                distance_along_route_m=400_000,
                score=StopScore(
                    preference_match=0.3, scenic_value=0.2, meal_fit=0.8,
                    timing_fit=0.5, detour_penalty=0.0, total_score=0.4,
                    selection_reason="test",
                ),
            ),
        ],
        segments=[
            Segment(from_name="Origin", to_name="Stop 1", distance_m=200_000, duration_s=7200),
            Segment(from_name="Stop 1", to_name="Stop 2", distance_m=200_000, duration_s=7200),
            Segment(from_name="Stop 2", to_name="Destination", distance_m=100_000, duration_s=3600),
        ],
        corridor=CorridorGeometry(
            route_polyline="",
            sample_points=[
                CorridorPoint(lat=37.0, lng=-122.0, distance_along_route_m=0, bearing=180),
                CorridorPoint(lat=34.0, lng=-118.0, distance_along_route_m=500_000, bearing=180),
            ],
            corridor_width_m=10000,
            total_distance_m=500_000,
        ),
        total_distance_m=500_000,
        total_duration_s=18000,
    )


@pytest.mark.asyncio
async def test_skip_and_replan_removes_stop():
    """Skipping a stop should remove it from the trip."""
    trip = _trip()
    maps = MagicMock()
    maps.get_route_with_waypoints = AsyncMock(return_value=[
        {"polyline": "", "distance_m": 400_000, "duration_s": 14400},
        {"polyline": "", "distance_m": 100_000, "duration_s": 3600},
    ])
    maps.get_route = AsyncMock(return_value={"polyline": "", "distance_m": 500_000, "duration_s": 18000})

    svc = RerouteService(maps)
    result = await svc.handle_skip_and_replan(trip, "stop1", 36.0, -121.0, visited_stop_ids=[])
    assert len(result.stops) == 1
    assert result.stops[0].id == "stop2"


@pytest.mark.asyncio
async def test_visited_stops_excluded():
    """Visited stops should not appear in rerouted trip."""
    trip = _trip()
    maps = MagicMock()
    maps.get_route_with_waypoints = AsyncMock(return_value=[
        {"polyline": "", "distance_m": 200_000, "duration_s": 7200},
    ])
    maps.get_route = AsyncMock(return_value={"polyline": "", "distance_m": 500_000, "duration_s": 18000})

    svc = RerouteService(maps)
    result = await svc.handle_skip_and_replan(trip, "stop1", 36.0, -121.0, visited_stop_ids=["stop2"])
    assert len(result.stops) == 0


@pytest.mark.asyncio
async def test_segment_rebuild():
    """Segments should be rebuilt after skip."""
    trip = _trip()
    maps = MagicMock()
    maps.get_route_with_waypoints = AsyncMock(return_value=[
        {"polyline": "abc", "distance_m": 300_000, "duration_s": 10800},
        {"polyline": "def", "distance_m": 200_000, "duration_s": 7200},
    ])

    svc = RerouteService(maps)
    result = await svc.handle_skip_and_replan(trip, "stop1", 36.0, -121.0, visited_stop_ids=[])
    assert len(result.segments) == 2  # Origin -> Stop2 -> Destination


@pytest.mark.asyncio
async def test_preferences_preserved():
    """User preferences should be preserved after rerouting."""
    trip = _trip()
    trip.preferences.interests = ["scenic", "food"]
    maps = MagicMock()
    maps.get_route_with_waypoints = AsyncMock(return_value=[
        {"polyline": "", "distance_m": 500_000, "duration_s": 18000},
    ])
    maps.get_route = AsyncMock(return_value={"polyline": "", "distance_m": 500_000, "duration_s": 18000})

    svc = RerouteService(maps)
    result = await svc.handle_skip_and_replan(trip, "stop1", 36.0, -121.0, visited_stop_ids=["stop2"])
    assert result.preferences.interests == ["scenic", "food"]


@pytest.mark.asyncio
async def test_full_reroute_calls_pipeline():
    """Full reroute should call the complete pipeline."""
    trip = _trip()
    maps = MagicMock()
    maps.get_route_from_coords = AsyncMock(return_value={
        "polyline": "encoded",
        "distance_m": 300_000,
        "duration_s": 10800,
    })
    maps.search_places_along_corridor = AsyncMock(return_value=[])
    maps.search_charging_stations = AsyncMock(return_value=[])
    maps.get_route_with_waypoints = AsyncMock(return_value=[])
    maps.get_route = AsyncMock(return_value={"polyline": "enc", "distance_m": 300_000, "duration_s": 10800})

    svc = RerouteService(maps)

    with patch("app.services.reroute_service.build_corridor") as mock_corridor:
        mock_corridor.return_value = CorridorGeometry(
            route_polyline="encoded",
            sample_points=[
                CorridorPoint(lat=35.0, lng=-119.0, distance_along_route_m=0, bearing=180),
                CorridorPoint(lat=34.0, lng=-118.0, distance_along_route_m=300_000, bearing=180),
            ],
            corridor_width_m=10000,
            total_distance_m=300_000,
        )
        result = await svc.reroute_from_position(trip, 35.5, -119.5, visited_stop_ids=["stop1"])

    maps.get_route_from_coords.assert_called_once()
    assert result.total_distance_m == 300_000
