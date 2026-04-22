"""Tests for the drive WebSocket and PolylineInterpolator."""

import pytest

from app.services.polyline_interpolator import PolylineInterpolator


class TestPolylineInterpolator:
    @pytest.fixture
    def points(self):
        # Simple 3-point route: (0,0) → (1,0) → (1,1)
        return [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]

    @pytest.fixture
    def interpolator(self, points):
        return PolylineInterpolator(points, total_duration_s=100.0)

    def test_position_at_start(self, interpolator):
        pos = interpolator.position_at_fraction(0.0)
        assert pos == (0.0, 0.0)

    def test_position_at_end(self, interpolator):
        pos = interpolator.position_at_fraction(1.0)
        assert pos == (1.0, 1.0)

    def test_position_at_midpoint(self, interpolator):
        pos = interpolator.position_at_fraction(0.5)
        # Should be near the midpoint of the route (around the bend)
        assert pos[0] == pytest.approx(1.0, abs=0.1)
        assert pos[1] == pytest.approx(0.0, abs=0.1)

    def test_position_clamps_below_zero(self, interpolator):
        pos = interpolator.position_at_fraction(-0.5)
        assert pos == (0.0, 0.0)

    def test_position_clamps_above_one(self, interpolator):
        pos = interpolator.position_at_fraction(1.5)
        assert pos == (1.0, 1.0)

    def test_advance_accumulates(self, interpolator):
        pos1 = interpolator.advance(10.0)  # 10% of 100s
        pos2 = interpolator.advance(10.0)  # 20% total
        # Should be different positions
        assert pos1 != pos2

    def test_advance_reaches_end(self, interpolator):
        pos = interpolator.advance(200.0)  # Well past total duration
        assert pos == (1.0, 1.0)

    def test_empty_points(self):
        interp = PolylineInterpolator([], total_duration_s=100.0)
        assert interp.position_at_fraction(0.5) == (0.0, 0.0)

    def test_single_point(self):
        interp = PolylineInterpolator([(5.0, 10.0)], total_duration_s=100.0)
        assert interp.position_at_fraction(0.0) == (5.0, 10.0)
        assert interp.position_at_fraction(1.0) == (5.0, 10.0)

    def test_total_distance_computed(self, interpolator, points):
        assert interpolator.total_dist > 0
        assert len(interpolator.cum_dists) == len(points)
