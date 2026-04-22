import math

import polyline as polyline_lib

from app.models.corridor import CorridorPoint

EARTH_RADIUS_M = 6_371_000


def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decode a Google-encoded polyline into a list of (lat, lng) tuples."""
    return polyline_lib.decode(encoded)


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the great-circle distance in meters between two points."""
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return the initial bearing in degrees from point 1 to point 2."""
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlng = lng2 - lng1
    x = math.sin(dlng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlng)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def point_to_segment_distance(
    plat: float, plng: float, alat: float, alng: float, blat: float, blng: float
) -> float:
    """
    Approximate perpendicular distance from point P to segment A-B.
    Projects P onto the line A-B and clamps to the segment endpoints.
    """
    ab = haversine(alat, alng, blat, blng)
    if ab < 1e-6:
        return haversine(plat, plng, alat, alng)

    ap = haversine(alat, alng, plat, plng)
    bp = haversine(blat, blng, plat, plng)

    # Project P onto AB using the cosine rule
    t = (ap**2 + ab**2 - bp**2) / (2 * ab)
    t = max(0.0, min(ab, t))

    # Perpendicular distance (approximate)
    if t <= 0:
        return ap
    if t >= ab:
        return bp
    return math.sqrt(max(0, ap**2 - t**2))


def distance_along_polyline(
    lat: float, lng: float, polyline_points: list[tuple[float, float]]
) -> tuple[float, int]:
    """
    Find the closest segment on the polyline to the given point.
    Returns (distance_along_route_m, nearest_segment_index).
    """
    min_dist = float("inf")
    best_along = 0.0
    best_idx = 0
    cumulative = 0.0

    for i in range(len(polyline_points) - 1):
        alat, alng = polyline_points[i]
        blat, blng = polyline_points[i + 1]
        seg_len = haversine(alat, alng, blat, blng)

        dist = point_to_segment_distance(lat, lng, alat, alng, blat, blng)

        if dist < min_dist:
            min_dist = dist
            # Compute how far along this segment the projection falls
            ap = haversine(alat, alng, lat, lng)
            bp = haversine(blat, blng, lat, lng)
            if seg_len < 1e-6:
                proj = 0.0
            else:
                proj = (ap**2 + seg_len**2 - bp**2) / (2 * seg_len)
                proj = max(0.0, min(seg_len, proj))
            best_along = cumulative + proj
            best_idx = i

        cumulative += seg_len

    return best_along, best_idx


def sample_polyline(
    points: list[tuple[float, float]], interval_m: float
) -> list[CorridorPoint]:
    """
    Sample points along a polyline at regular intervals.
    Returns CorridorPoints with distance_along_route_m and bearing.
    """
    if len(points) < 2:
        if points:
            return [CorridorPoint(lat=points[0][0], lng=points[0][1], distance_along_route_m=0.0, bearing=0.0)]
        return []

    samples: list[CorridorPoint] = []
    cumulative = 0.0
    next_sample_at = 0.0

    # Always include the first point
    b = bearing(points[0][0], points[0][1], points[1][0], points[1][1])
    samples.append(CorridorPoint(lat=points[0][0], lng=points[0][1], distance_along_route_m=0.0, bearing=b))
    next_sample_at = interval_m

    for i in range(len(points) - 1):
        seg_start = points[i]
        seg_end = points[i + 1]
        seg_len = haversine(seg_start[0], seg_start[1], seg_end[0], seg_end[1])
        seg_bearing = bearing(seg_start[0], seg_start[1], seg_end[0], seg_end[1])

        while next_sample_at <= cumulative + seg_len:
            frac = (next_sample_at - cumulative) / seg_len if seg_len > 0 else 0
            lat = seg_start[0] + frac * (seg_end[0] - seg_start[0])
            lng = seg_start[1] + frac * (seg_end[1] - seg_start[1])
            samples.append(
                CorridorPoint(
                    lat=lat,
                    lng=lng,
                    distance_along_route_m=next_sample_at,
                    bearing=seg_bearing,
                )
            )
            next_sample_at += interval_m

        cumulative += seg_len

    # Always include the last point
    last = points[-1]
    last_bearing = bearing(points[-2][0], points[-2][1], last[0], last[1])
    if not samples or haversine(samples[-1].lat, samples[-1].lng, last[0], last[1]) > 100:
        samples.append(
            CorridorPoint(lat=last[0], lng=last[1], distance_along_route_m=cumulative, bearing=last_bearing)
        )

    return samples
