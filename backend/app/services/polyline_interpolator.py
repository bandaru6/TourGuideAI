"""
Utility for advancing a simulated position along a decoded polyline.
Used by the drive WebSocket for server-side simulation.
"""

from app.engine.geo_utils import haversine


class PolylineInterpolator:
    """Interpolates position along a polyline based on elapsed time."""

    def __init__(self, points: list[tuple[float, float]], total_duration_s: float):
        self.points = points
        self.total_duration_s = max(total_duration_s, 1.0)
        self.elapsed_s = 0.0

        # Precompute cumulative distances
        self.cum_dists: list[float] = [0.0]
        for i in range(1, len(points)):
            d = haversine(
                points[i - 1][0], points[i - 1][1],
                points[i][0], points[i][1],
            )
            self.cum_dists.append(self.cum_dists[-1] + d)
        self.total_dist = self.cum_dists[-1] if self.cum_dists else 0.0

    def advance(self, dt_s: float) -> tuple[float, float]:
        """Advance by dt_s seconds and return (lat, lng)."""
        self.elapsed_s += dt_s
        fraction = min(self.elapsed_s / self.total_duration_s, 1.0)
        return self._position_at_fraction(fraction)

    def position_at_fraction(self, fraction: float) -> tuple[float, float]:
        """Get position at a given fraction (0-1) along the route."""
        return self._position_at_fraction(min(max(fraction, 0.0), 1.0))

    def _position_at_fraction(self, fraction: float) -> tuple[float, float]:
        if not self.points:
            return (0.0, 0.0)
        if fraction <= 0:
            return self.points[0]
        if fraction >= 1:
            return self.points[-1]

        target_dist = fraction * self.total_dist

        for i in range(1, len(self.cum_dists)):
            if self.cum_dists[i] >= target_dist:
                seg_start = self.cum_dists[i - 1]
                seg_len = self.cum_dists[i] - seg_start
                if seg_len < 1e-6:
                    return self.points[i - 1]
                seg_frac = (target_dist - seg_start) / seg_len
                lat = self.points[i - 1][0] + seg_frac * (self.points[i][0] - self.points[i - 1][0])
                lng = self.points[i - 1][1] + seg_frac * (self.points[i][1] - self.points[i - 1][1])
                return (lat, lng)

        return self.points[-1]
