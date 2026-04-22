"""Tests for GeminiService with mocked HTTP calls."""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.gemini_service import GeminiService
from app.models.trip import Trip, Stop
from app.models.preferences import UserPreferences
from app.models.drive_events import TripState


def _make_trip(stops=None):
    return Trip(
        origin="San Francisco",
        destination="Los Angeles",
        preferences=UserPreferences(),
        state=TripState.READY,
        stops=stops or [],
        segments=[],
        corridor=None,
        total_distance_m=500000,
        total_duration_s=18000,
        route_polyline="abc",
    )


def _make_stop(name="Half Moon Bay", stop_type="beach"):
    return Stop(
        id="stop1",
        name=name,
        type=stop_type,
        lat=37.5,
        lng=-122.4,
        place_id="osm_1",
        description="",
        photos=[],
        suggested_duration_min=30,
        distance_along_route_m=50000,
        detour_distance_m=2000,
        score=None,
        fun_facts=[],
    )


class TestGeminiService:
    def test_disabled_without_api_key(self):
        svc = GeminiService("")
        assert not svc.enabled

    def test_enabled_with_api_key(self):
        svc = GeminiService("test-key-123")
        assert svc.enabled

    async def test_enrich_skips_when_disabled(self):
        svc = GeminiService("")
        trip = _make_trip([_make_stop()])
        result = await svc.enrich_trip(trip)
        assert result is trip
        assert result.stops[0].description == ""
        assert len(result.stops[0].fun_facts) == 0

    async def test_enrich_skips_empty_stops(self):
        svc = GeminiService("test-key")
        trip = _make_trip([])
        result = await svc.enrich_trip(trip)
        assert result is trip

    async def test_enrich_applies_enrichment(self):
        svc = GeminiService("test-key")
        trip = _make_trip([_make_stop("Half Moon Bay")])

        enrichment_data = {
            "Half Moon Bay": {
                "description": "A beautiful coastal town.",
                "fun_facts": ["Home to the Mavericks surf competition."],
            }
        }

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": json.dumps(enrichment_data)}]
                }
            }]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await svc.enrich_trip(trip)

        assert result.stops[0].description == "A beautiful coastal town."
        assert len(result.stops[0].fun_facts) == 1
        assert "Mavericks" in result.stops[0].fun_facts[0].text

    async def test_enrich_graceful_on_api_error(self):
        svc = GeminiService("test-key")
        trip = _make_trip([_make_stop()])

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("API down"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await svc.enrich_trip(trip)

        # Should return trip unchanged, not raise
        assert result is trip
        assert result.stops[0].description == ""

    def test_build_prompt(self):
        svc = GeminiService("test-key")
        prompt = svc._build_prompt("SF", "LA", ["Half Moon Bay", "Santa Barbara"])
        assert "SF" in prompt
        assert "LA" in prompt
        assert "Half Moon Bay" in prompt
        assert "Santa Barbara" in prompt
        assert "fun_facts" in prompt
