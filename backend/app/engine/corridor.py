from app.engine.geo_utils import decode_polyline, haversine, sample_polyline
from app.models.corridor import CorridorGeometry, CorridorPoint


def build_corridor(
    polyline_encoded: str,
    interval_m: float = 16000,
    width_m: float = 8000,
) -> CorridorGeometry:
    """
    Build a route corridor from an encoded polyline.
    Samples points at interval_m spacing with a corridor width of width_m.
    """
    points = decode_polyline(polyline_encoded)
    sample_points = sample_polyline(points, interval_m)

    total_distance = 0.0
    for i in range(len(points) - 1):
        total_distance += haversine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

    return CorridorGeometry(
        route_polyline=polyline_encoded,
        sample_points=sample_points,
        corridor_width_m=width_m,
        total_distance_m=total_distance,
    )


def find_nearest_corridor_point(
    lat: float, lng: float, corridor: CorridorGeometry
) -> tuple[CorridorPoint, float]:
    """
    Find the nearest corridor sample point to the given location.
    Returns (nearest_point, distance_in_meters).
    """
    min_dist = float("inf")
    nearest = corridor.sample_points[0]

    for pt in corridor.sample_points:
        d = haversine(lat, lng, pt.lat, pt.lng)
        if d < min_dist:
            min_dist = d
            nearest = pt

    return nearest, min_dist


def is_within_corridor(lat: float, lng: float, corridor: CorridorGeometry) -> bool:
    """Check if a point is within the corridor width of any sample point."""
    _, dist = find_nearest_corridor_point(lat, lng, corridor)
    return dist <= corridor.corridor_width_m
