"""
Traffic-aware ETA engine.

Deterministic time-of-day heuristic for congestion estimation.
No external API required — uses predictable rush hour patterns.
"""

from app.models.trip import Segment, Stop


def estimate_congestion(
    lat: float, lng: float, time_of_day_h: float, day_of_week: int
) -> float:
    """
    Estimate congestion factor 0.0-1.0 based on time of day and day of week.

    Rush hours: 7-9 AM and 4-6 PM on weekdays score higher.
    Weekends have lower base congestion.
    """
    # Weekend: lower congestion
    if day_of_week >= 5:  # Saturday=5, Sunday=6
        base = 0.1
    else:
        base = 0.2

    # Morning rush: 7-9
    if 7 <= time_of_day_h < 9:
        rush = 0.6 if day_of_week < 5 else 0.2
    # Evening rush: 16-18
    elif 16 <= time_of_day_h < 18:
        rush = 0.7 if day_of_week < 5 else 0.25
    # Shoulder hours: 9-10, 15-16
    elif 9 <= time_of_day_h < 10 or 15 <= time_of_day_h < 16:
        rush = 0.3 if day_of_week < 5 else 0.1
    # Late night: 22-6
    elif time_of_day_h >= 22 or time_of_day_h < 6:
        rush = 0.0
        base = 0.05
    else:
        rush = 0.15

    return min(1.0, base + rush)


def adjust_segment_duration(base_s: float, congestion: float) -> float:
    """Adjust segment duration by congestion factor. Max 80% increase."""
    return base_s * (1 + congestion * 0.8)


def apply_traffic_to_segments(
    segments: list[Segment],
    departure_hour: float = 9.0,
    day_of_week: int = 1,
) -> list[Segment]:
    """Apply traffic adjustments to all segments, accumulating time of day."""
    current_hour = departure_hour
    for seg in segments:
        # Use midpoint estimate for congestion
        mid_hour = current_hour + (seg.duration_s / 3600) / 2
        congestion = estimate_congestion(0, 0, mid_hour % 24, day_of_week)
        seg.traffic_factor = round(congestion, 3)
        seg.adjusted_duration_s = round(adjust_segment_duration(seg.duration_s, congestion), 1)
        current_hour += seg.adjusted_duration_s / 3600
    return segments


def suggest_drops(
    stops: list[Stop], behind_schedule_s: float
) -> list[Stop]:
    """
    Suggest stops to drop when behind schedule.
    Drops lowest-scored stops first until recovered time >= behind_schedule_s.
    """
    if behind_schedule_s <= 0:
        return []

    # Sort by score ascending (drop lowest first)
    sortable = [
        s for s in stops
        if s.score is not None
    ]
    sortable.sort(key=lambda s: s.score.total_score)

    to_drop: list[Stop] = []
    recovered_s = 0.0
    for s in sortable:
        to_drop.append(s)
        recovered_s += s.suggested_duration_min * 60
        if recovered_s >= behind_schedule_s:
            break

    return to_drop
