"""Tests for MapsService with mocked HTTP calls."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.maps_service import MapsService, _osm_tags_to_types, _geocode_cache, _cache_key


class TestOsmTagsToTypes:
    def test_viewpoint(self):
        types = _osm_tags_to_types({"tourism": "viewpoint"})
        assert "tourist_attraction" in types
        assert "point_of_interest" in types

    def test_restaurant(self):
        types = _osm_tags_to_types({"amenity": "restaurant"})
        assert "restaurant" in types
        assert "food" in types

    def test_beach(self):
        types = _osm_tags_to_types({"natural": "beach"})
        assert "beach" in types

    def test_museum(self):
        types = _osm_tags_to_types({"tourism": "museum"})
        assert "museum" in types
        assert "tourist_attraction" in types

    def test_park(self):
        types = _osm_tags_to_types({"leisure": "park"})
        assert "park" in types

    def test_unknown_tags(self):
        types = _osm_tags_to_types({"building": "yes"})
        assert types == ["point_of_interest"]

    def test_historic(self):
        types = _osm_tags_to_types({"historic": "castle"})
        assert "museum" in types
        assert "tourist_attraction" in types

    def test_cafe(self):
        types = _osm_tags_to_types({"amenity": "cafe"})
        assert "cafe" in types
        assert "food" in types

    def test_gas_station(self):
        types = _osm_tags_to_types({"amenity": "fuel"})
        assert "gas_station" in types

    def test_wildcard_shop(self):
        types = _osm_tags_to_types({"shop": "supermarket"})
        assert "store" in types


class TestGeocodeCaching:
    def test_cache_key_normalization(self):
        k1 = _cache_key("San Francisco, CA")
        k2 = _cache_key("san francisco, ca")
        k3 = _cache_key("  San Francisco, CA  ")
        assert k1 == k2
        assert k1 == k3

    def test_different_addresses_different_keys(self):
        k1 = _cache_key("San Francisco, CA")
        k2 = _cache_key("Los Angeles, CA")
        assert k1 != k2


class TestMapsService:
    @pytest.fixture
    def service(self):
        return MapsService()

    async def test_geocode_returns_lat_lng(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"lat": "37.7749", "lon": "-122.4194"}]
        mock_response.raise_for_status = MagicMock()

        # Clear cache
        _geocode_cache.clear()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            lat, lng = await service._geocode("San Francisco, CA")
            assert lat == pytest.approx(37.7749)
            assert lng == pytest.approx(-122.4194)

    async def test_geocode_caches_result(self, service):
        _geocode_cache.clear()
        key = _cache_key("Test City")
        _geocode_cache[key] = (40.0, -74.0)

        lat, lng = await service._geocode("Test City")
        assert lat == 40.0
        assert lng == -74.0

    async def test_geocode_empty_result_raises(self, service):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        _geocode_cache.clear()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ValueError, match="Could not geocode"):
                await service._geocode("Nonexistent Place XYZ123")

    async def test_get_route_success(self, service):
        _geocode_cache.clear()
        _geocode_cache[_cache_key("A")] = (37.0, -122.0)
        _geocode_cache[_cache_key("B")] = (34.0, -118.0)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": "Ok",
            "routes": [{
                "geometry": "abc123",
                "distance": 500000,
                "duration": 18000,
            }],
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await service.get_route("A", "B")
            assert result["polyline"] == "abc123"
            assert result["distance_m"] == 500000
            assert result["duration_s"] == 18000

    async def test_get_route_failure(self, service):
        _geocode_cache.clear()
        _geocode_cache[_cache_key("A")] = (37.0, -122.0)
        _geocode_cache[_cache_key("B")] = (34.0, -118.0)

        mock_response = MagicMock()
        mock_response.json.return_value = {"code": "NoRoute", "routes": []}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(ValueError, match="OSRM routing failed"):
                await service.get_route("A", "B")
