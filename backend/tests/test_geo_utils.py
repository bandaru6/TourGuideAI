import pytest
from app.engine.geo_utils import (
    decode_polyline,
    haversine,
    bearing,
    point_to_segment_distance,
    distance_along_polyline,
    sample_polyline,
)


class TestHaversine:
    def test_same_point(self):
        assert haversine(37.7749, -122.4194, 37.7749, -122.4194) == 0.0

    def test_sf_to_la(self):
        # SF to LA is roughly 559 km
        dist = haversine(37.7749, -122.4194, 34.0522, -118.2437)
        assert 550_000 < dist < 570_000

    def test_short_distance(self):
        # ~111 meters per 0.001 degrees of latitude
        dist = haversine(37.0, -122.0, 37.001, -122.0)
        assert 100 < dist < 120

    def test_symmetry(self):
        d1 = haversine(37.7749, -122.4194, 34.0522, -118.2437)
        d2 = haversine(34.0522, -118.2437, 37.7749, -122.4194)
        assert abs(d1 - d2) < 0.01


class TestBearing:
    def test_due_north(self):
        b = bearing(37.0, -122.0, 38.0, -122.0)
        assert abs(b - 0.0) < 1.0

    def test_due_east(self):
        b = bearing(37.0, -122.0, 37.0, -121.0)
        assert 89 < b < 91

    def test_due_south(self):
        b = bearing(38.0, -122.0, 37.0, -122.0)
        assert 179 < b < 181


class TestDecodePolyline:
    def test_decode_simple(self):
        # Known encoded polyline for a simple path
        encoded = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        points = decode_polyline(encoded)
        assert len(points) == 3
        assert abs(points[0][0] - 38.5) < 0.1
        assert abs(points[0][1] - (-120.2)) < 0.1

    def test_decode_empty(self):
        points = decode_polyline("")
        assert points == []


class TestPointToSegmentDistance:
    def test_point_on_segment(self):
        # Point very close to the midpoint of a N-S segment
        dist = point_to_segment_distance(37.5, -122.0, 37.0, -122.0, 38.0, -122.0)
        assert dist < 100  # should be essentially 0

    def test_point_off_segment(self):
        # Point 1 degree east of a N-S segment
        dist = point_to_segment_distance(37.5, -121.0, 37.0, -122.0, 38.0, -122.0)
        assert dist > 80_000  # roughly 85 km


class TestDistanceAlongPolyline:
    def test_start_point(self):
        points = [(37.0, -122.0), (37.5, -122.0), (38.0, -122.0)]
        along, idx = distance_along_polyline(37.0, -122.0, points)
        assert along < 100
        assert idx == 0

    def test_midpoint(self):
        points = [(37.0, -122.0), (37.5, -122.0), (38.0, -122.0)]
        along, idx = distance_along_polyline(37.5, -122.0, points)
        total = haversine(37.0, -122.0, 38.0, -122.0)
        assert abs(along - total / 2) < 1000  # within 1km of midpoint

    def test_end_point(self):
        points = [(37.0, -122.0), (37.5, -122.0), (38.0, -122.0)]
        along, idx = distance_along_polyline(38.0, -122.0, points)
        total = haversine(37.0, -122.0, 38.0, -122.0)
        assert abs(along - total) < 1000


class TestSamplePolyline:
    def test_basic_sampling(self):
        points = [(37.0, -122.0), (38.0, -122.0)]
        total = haversine(37.0, -122.0, 38.0, -122.0)
        interval = total / 4

        samples = sample_polyline(points, interval)
        assert len(samples) >= 4
        assert samples[0].distance_along_route_m == 0.0
        assert samples[-1].distance_along_route_m > 0

    def test_single_point(self):
        samples = sample_polyline([(37.0, -122.0)], 1000)
        assert len(samples) == 1

    def test_empty(self):
        samples = sample_polyline([], 1000)
        assert len(samples) == 0
