"""
Multi-stop constraint solver with beam search.

Handles time windows, per-stop detour limits, and EV charging insertion.
Falls back to greedy itinerary on failure.
"""

import uuid
from dataclasses import dataclass

from app.engine.geo_utils import haversine
from app.models.corridor import CorridorGeometry
from app.models.preferences import UserPreferences
from app.models.scoring import StopScore
from app.models.trip import CandidateStop, Stop, StopType


@dataclass
class StopConstraint:
    open_hour: float | None = None    # e.g. 8.0
    close_hour: float | None = None   # e.g. 20.0
    best_time_start: float | None = None
    best_time_end: float | None = None
    max_detour_m: float | None = None
    is_charging_stop: bool = False
    charge_time_min: int = 30


def _parse_opening_hours(hours_str: str | None) -> tuple[float | None, float | None]:
    """Parse simple 'HH:MM-HH:MM' format to (open_hour, close_hour)."""
    if not hours_str:
        return None, None
    try:
        parts = hours_str.split("-")
        if len(parts) != 2:
            return None, None
        open_h, open_m = parts[0].strip().split(":")
        close_h, close_m = parts[1].strip().split(":")
        return int(open_h) + int(open_m) / 60, int(close_h) + int(close_m) / 60
    except (ValueError, IndexError):
        return None, None


def _estimate_arrival_hour(
    departure_hour: float,
    distance_along_route_m: float,
    total_distance_m: float,
    base_duration_s: float,
    stop_time_so_far_s: float,
) -> float:
    """Linear interpolation of arrival time from departure."""
    if total_distance_m <= 0:
        return departure_hour
    fraction = distance_along_route_m / total_distance_m
    travel_s = fraction * base_duration_s + stop_time_so_far_s
    return (departure_hour + travel_s / 3600) % 24


# Stop type inference (mirrors itinerary.py)
from app.engine.itinerary import _infer_stop_type, _estimate_duration


class ConstraintSolver:
    """
    Beam search constraint solver for multi-stop route optimization.

    Improvements over greedy:
    - Time window validation (arrival within open hours)
    - Per-stop detour limits
    - EV charging insertion
    - Beam search explores multiple candidate orderings
    """

    def __init__(
        self,
        ranked_candidates: list[tuple[CandidateStop, StopScore]],
        corridor: CorridorGeometry,
        preferences: UserPreferences,
        base_duration_s: float = 21600,
        departure_hour: float = 9.0,
        charging_candidates: list[CandidateStop] | None = None,
    ):
        self.ranked = ranked_candidates
        self.corridor = corridor
        self.preferences = preferences
        self.base_duration_s = base_duration_s
        self.departure_hour = departure_hour
        self.charging_candidates = charging_candidates or []
        self.total_distance = corridor.total_distance_m

    def solve(self, beam_width: int = 10) -> list[Stop]:
        """
        Beam search forward pass with constraint pruning.
        Returns ordered list of Stops.
        """
        if not self.ranked or self.total_distance <= 0:
            return []

        avg_speed_ms = 100 * 1000 / 3600
        min_spacing_m = self.preferences.stop_interval_min * 60 * avg_speed_ms
        max_total_detour = self.total_distance * 0.20
        per_stop_detour_limit_m = None
        if self.preferences.max_detour_per_stop_min is not None:
            per_stop_detour_limit_m = self.preferences.max_detour_per_stop_min * 60 * avg_speed_ms

        # Sort by distance along route
        sorted_candidates = sorted(self.ranked, key=lambda x: x[0].distance_along_route_m)

        # Beam state: (selected list, last_stop_distance, total_detour, total_stop_time_s, score_sum)
        BeamState = tuple[
            list[tuple[CandidateStop, StopScore]], float, float, float, float
        ]
        beam: list[BeamState] = [([], 0.0, 0.0, 0.0, 0.0)]

        for candidate, score in sorted_candidates:
            next_beam: list[BeamState] = []

            for state in beam:
                selected, last_dist, total_detour, total_stop_time, score_sum = state

                # Option 1: skip this candidate
                next_beam.append(state)

                # Option 2: include this candidate (if constraints pass)
                gap = candidate.distance_along_route_m - last_dist
                if gap < min_spacing_m and selected:
                    continue

                if total_detour + candidate.distance_to_route_m > max_total_detour:
                    continue

                if per_stop_detour_limit_m and candidate.distance_to_route_m > per_stop_detour_limit_m:
                    continue

                # Time window check
                arrival_h = _estimate_arrival_hour(
                    self.departure_hour,
                    candidate.distance_along_route_m,
                    self.total_distance,
                    self.base_duration_s,
                    total_stop_time,
                )
                open_h, close_h = _parse_opening_hours(candidate.opening_hours)
                if open_h is not None and close_h is not None:
                    if not (open_h <= arrival_h <= close_h):
                        continue

                stop_type = _infer_stop_type(candidate.types)
                duration = _estimate_duration(stop_type)
                new_stop_time = total_stop_time + duration * 60

                if new_stop_time > self.base_duration_s * 0.5:
                    continue

                new_selected = selected + [(candidate, score)]
                next_beam.append((
                    new_selected,
                    candidate.distance_along_route_m,
                    total_detour + candidate.distance_to_route_m,
                    new_stop_time,
                    score_sum + score.total_score,
                ))

            # Prune beam: keep top beam_width by score_sum
            next_beam.sort(key=lambda s: s[4], reverse=True)
            beam = next_beam[:beam_width]

        if not beam:
            return []

        # Pick best beam (highest score sum)
        best = max(beam, key=lambda s: s[4])
        selected_pairs = best[0]

        # EV charging insertion
        if self.preferences.vehicle_range_km and self.charging_candidates:
            selected_pairs = self._insert_charging(selected_pairs)

        # Convert to Stop objects
        stops = []
        stop_time_so_far_s = 0.0
        for candidate, score in selected_pairs:
            stop_type = _infer_stop_type(candidate.types)
            duration = _estimate_duration(stop_type)

            arrival_h = _estimate_arrival_hour(
                self.departure_hour,
                candidate.distance_along_route_m,
                self.total_distance,
                self.base_duration_s,
                stop_time_so_far_s,
            )
            arrival_time_str = f"{int(arrival_h):02d}:{int((arrival_h % 1) * 60):02d}"

            open_h, close_h = _parse_opening_hours(candidate.opening_hours)
            open_hours_str = candidate.opening_hours

            stops.append(Stop(
                id=str(uuid.uuid4()),
                name=candidate.name,
                type=stop_type,
                lat=candidate.lat,
                lng=candidate.lng,
                place_id=candidate.place_id,
                suggested_duration_min=duration,
                distance_along_route_m=candidate.distance_along_route_m,
                detour_distance_m=candidate.distance_to_route_m,
                score=StopScore(
                    preference_match=score.preference_match,
                    scenic_value=score.scenic_value,
                    meal_fit=score.meal_fit,
                    timing_fit=score.timing_fit,
                    detour_penalty=score.detour_penalty,
                    congestion_penalty=score.congestion_penalty,
                    total_score=score.total_score,
                    selection_reason=score.selection_reason,
                    cluster_count=score.cluster_count,
                ),
                estimated_arrival_time=arrival_time_str,
                open_hours=open_hours_str,
            ))
            stop_time_so_far_s += duration * 60

        return stops

    def _insert_charging(
        self,
        selected: list[tuple[CandidateStop, StopScore]],
    ) -> list[tuple[CandidateStop, StopScore]]:
        """Insert EV charging stops when vehicle range would be exceeded."""
        if not self.preferences.vehicle_range_km:
            return selected

        range_m = self.preferences.vehicle_range_km * 1000
        result: list[tuple[CandidateStop, StopScore]] = []
        distance_since_charge = 0.0
        last_distance = 0.0

        for candidate, score in selected:
            gap = candidate.distance_along_route_m - last_distance
            distance_since_charge += gap

            if distance_since_charge > range_m * 0.8:
                # Need charging before this stop
                charging = self._find_charging_stop(last_distance, candidate.distance_along_route_m)
                if charging:
                    charge_score = StopScore(
                        preference_match=0.0,
                        scenic_value=0.0,
                        meal_fit=0.0,
                        timing_fit=0.5,
                        detour_penalty=0.0,
                        congestion_penalty=0.0,
                        total_score=0.3,
                        selection_reason=f"{charging.name}: EV charging stop",
                    )
                    result.append((charging, charge_score))
                    distance_since_charge = candidate.distance_along_route_m - charging.distance_along_route_m

            result.append((candidate, score))
            last_distance = candidate.distance_along_route_m

        return result

    def _find_charging_stop(
        self,
        after_m: float,
        before_m: float,
    ) -> CandidateStop | None:
        """Find a charging station between two route distances."""
        best = None
        best_dist = float("inf")
        midpoint = (after_m + before_m) / 2

        for c in self.charging_candidates:
            if after_m < c.distance_along_route_m < before_m:
                dist_to_mid = abs(c.distance_along_route_m - midpoint)
                if dist_to_mid < best_dist:
                    best = c
                    best_dist = dist_to_mid

        return best
