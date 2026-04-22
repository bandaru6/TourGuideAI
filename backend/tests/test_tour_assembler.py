"""Tests for TourAssembler pipeline with mocked services."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.config import Settings
from app.services.tour_assembler import TourAssembler
from app.models.trip import Trip, CandidateStop
from app.models.preferences import UserPreferences
from app.models.drive_events import TripState
from app.models.corridor import CorridorGeometry, CorridorPoint
from app.models.scoring import StopScore
from app.models.trip import Stop


def _make_trip():
    return Trip(
        origin="San Francisco",
        destination="Los Angeles",
        preferences=UserPreferences(interests=["beach", "scenic"]),
        state=TripState.GENERATING,
    )


def _make_corridor():
    return CorridorGeometry(
        route_polyline="abc123",
        sample_points=[
            CorridorPoint(lat=37.0 + i * 0.5, lng=-122.0 + i * 0.5, distance_along_route_m=i * 50000, bearing=180.0)
            for i in range(10)
        ],
        corridor_width_m=8000,
        total_distance_m=500000,
    )


def _make_candidate(name, lat, along_m):
    return CandidateStop(
        place_id=f"osm_{name}",
        name=name,
        lat=lat,
        lng=-122.0,
        types=["beach", "natural_feature"],
        rating=4.5,
        distance_to_route_m=1000,
        distance_along_route_m=along_m,
        nearest_corridor_point_idx=0,
    )


class TestTourAssembler:
    @pytest.fixture
    def settings(self):
        return Settings(
            google_maps_api_key="",
            gemini_api_key="",
        )

    @pytest.fixture
    def assembler(self, settings):
        return TourAssembler(settings)

    async def test_generate_trip_success(self, assembler):
        trip = _make_trip()
        corridor = _make_corridor()
        candidates = [
            _make_candidate("Beach A", 37.5, 100000),
            _make_candidate("Beach B", 36.5, 300000),
        ]
        stops = [
            Stop(name="Beach A", lat=37.5, lng=-122.0, place_id="osm_Beach A",
                 distance_along_route_m=100000, detour_distance_m=1000),
            Stop(name="Beach B", lat=36.5, lng=-122.0, place_id="osm_Beach B",
                 distance_along_route_m=300000, detour_distance_m=1000),
        ]

        mock_store = AsyncMock()

        with patch.object(assembler.maps, "get_route", new_callable=AsyncMock) as mock_route, \
             patch("app.services.tour_assembler.build_corridor") as mock_corridor, \
             patch.object(assembler.maps, "search_places_along_corridor", new_callable=AsyncMock) as mock_search, \
             patch("app.services.tour_assembler.rank_candidates") as mock_rank, \
             patch("app.services.tour_assembler.build_itinerary") as mock_itin, \
             patch.object(assembler.maps, "get_route_with_waypoints", new_callable=AsyncMock) as mock_segments, \
             patch.object(assembler.gemini, "enrich_trip", new_callable=AsyncMock) as mock_gemini:

            mock_route.return_value = {
                "polyline": "encoded_poly",
                "distance_m": 500000,
                "duration_s": 18000,
            }
            mock_corridor.return_value = corridor
            mock_search.return_value = candidates
            mock_rank.return_value = candidates
            mock_itin.return_value = stops
            mock_segments.return_value = [
                {"polyline": "seg1", "distance_m": 100000, "duration_s": 3600},
                {"polyline": "seg2", "distance_m": 200000, "duration_s": 7200},
                {"polyline": "seg3", "distance_m": 200000, "duration_s": 7200},
            ]
            mock_gemini.side_effect = lambda t: t

            result = await assembler.generate_trip(trip, mock_store)

        assert result.state == TripState.READY
        assert result.route_polyline == "encoded_poly"
        assert result.total_distance_m == 500000
        assert result.total_duration_s == 18000
        assert len(result.stops) == 2
        mock_store.save.assert_called()

    async def test_generate_trip_no_candidates(self, assembler):
        trip = _make_trip()
        corridor = _make_corridor()

        mock_store = AsyncMock()

        with patch.object(assembler.maps, "get_route", new_callable=AsyncMock) as mock_route, \
             patch("app.services.tour_assembler.build_corridor") as mock_corridor, \
             patch.object(assembler.maps, "search_places_along_corridor", new_callable=AsyncMock) as mock_search:

            mock_route.return_value = {
                "polyline": "encoded_poly",
                "distance_m": 100000,
                "duration_s": 3600,
            }
            mock_corridor.return_value = corridor
            mock_search.return_value = []

            result = await assembler.generate_trip(trip, mock_store)

        assert result.state == TripState.READY
        assert len(result.stops) == 0
        assert len(result.segments) == 1  # Direct segment origin → dest

    async def test_generate_trip_route_failure(self, assembler):
        trip = _make_trip()
        mock_store = AsyncMock()

        with patch.object(assembler.maps, "get_route", new_callable=AsyncMock) as mock_route:
            mock_route.side_effect = ValueError("OSRM routing failed")

            result = await assembler.generate_trip(trip, mock_store)

        assert result.state == TripState.DRAFT  # Reset on failure
        mock_store.save.assert_called()

    async def test_generate_trip_sets_corridor(self, assembler):
        trip = _make_trip()
        corridor = _make_corridor()
        mock_store = AsyncMock()

        with patch.object(assembler.maps, "get_route", new_callable=AsyncMock) as mock_route, \
             patch("app.services.tour_assembler.build_corridor") as mock_corridor, \
             patch.object(assembler.maps, "search_places_along_corridor", new_callable=AsyncMock) as mock_search:

            mock_route.return_value = {
                "polyline": "poly",
                "distance_m": 100000,
                "duration_s": 3600,
            }
            mock_corridor.return_value = corridor
            mock_search.return_value = []

            result = await assembler.generate_trip(trip, mock_store)

        assert result.corridor is not None
        assert result.corridor.total_distance_m == 500000
