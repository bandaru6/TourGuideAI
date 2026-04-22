import pytest
from app.engine.corridor import build_corridor, find_nearest_corridor_point, is_within_corridor
from app.engine.geo_utils import haversine

import polyline as polyline_lib


def _encode_path(points: list[tuple[float, float]]) -> str:
    return polyline_lib.encode(points)


class TestBuildCorridor:
    def test_basic_corridor(self):
        # Simple N-S path
        path = [(37.0, -122.0), (37.5, -122.0), (38.0, -122.0)]
        encoded = _encode_path(path)

        corridor = build_corridor(encoded, interval_m=20000, width_m=5000)

        assert corridor.corridor_width_m == 5000
        assert corridor.total_distance_m > 0
        assert len(corridor.sample_points) >= 2
        assert corridor.route_polyline == encoded

    def test_corridor_points_ordered(self):
        path = [(34.0, -118.0), (35.0, -119.0), (36.0, -120.0), (37.0, -121.0)]
        encoded = _encode_path(path)
        corridor = build_corridor(encoded, interval_m=30000)

        distances = [p.distance_along_route_m for p in corridor.sample_points]
        assert distances == sorted(distances)

    def test_total_distance(self):
        path = [(37.0, -122.0), (38.0, -122.0)]
        encoded = _encode_path(path)
        corridor = build_corridor(encoded)

        expected = haversine(37.0, -122.0, 38.0, -122.0)
        assert abs(corridor.total_distance_m - expected) < 100


class TestFindNearestCorridorPoint:
    def test_on_route(self):
        path = [(37.0, -122.0), (38.0, -122.0)]
        encoded = _encode_path(path)
        corridor = build_corridor(encoded, interval_m=20000)

        pt, dist = find_nearest_corridor_point(37.5, -122.0, corridor)
        assert dist < 5000  # Should be close to a sample point

    def test_far_from_route(self):
        path = [(37.0, -122.0), (38.0, -122.0)]
        encoded = _encode_path(path)
        corridor = build_corridor(encoded, interval_m=20000)

        pt, dist = find_nearest_corridor_point(37.5, -120.0, corridor)
        assert dist > 100_000  # ~170km away


class TestIsWithinCorridor:
    def test_point_on_route(self):
        path = [(37.0, -122.0), (38.0, -122.0)]
        encoded = _encode_path(path)
        corridor = build_corridor(encoded, interval_m=20000, width_m=10000)

        assert is_within_corridor(37.5, -122.0, corridor)

    def test_point_outside_corridor(self):
        path = [(37.0, -122.0), (38.0, -122.0)]
        encoded = _encode_path(path)
        corridor = build_corridor(encoded, interval_m=20000, width_m=5000)

        assert not is_within_corridor(37.5, -120.0, corridor)
