import uuid

from app.models.corridor import CorridorGeometry
from app.models.preferences import UserPreferences
from app.models.scoring import StopScore
from app.models.trip import CandidateStop, Stop, StopType

from app.engine.ranking import RESTAURANT_TYPES, SCENIC_TYPES, CULTURE_TYPES, OUTDOOR_TYPES

# Stop type inference from Google Places types
TYPE_MAPPING: list[tuple[set[str], StopType]] = [
    ({"beach"}, StopType.BEACH),
    ({"park", "campground"}, StopType.PARK),
    ({"museum", "art_gallery"}, StopType.MUSEUM),
    ({"restaurant", "cafe", "bakery", "food"}, StopType.RESTAURANT),
    ({"cafe"}, StopType.CAFE),
    ({"gas_station"}, StopType.GAS_STATION),
    ({"natural_feature", "point_of_interest"}, StopType.SCENIC),
    ({"tourist_attraction", "amusement_park", "zoo", "aquarium"}, StopType.ATTRACTION),
]


def _infer_stop_type(types: list[str]) -> StopType:
    candidate_types = set(types)
    for type_set, stop_type in TYPE_MAPPING:
        if candidate_types & type_set:
            return stop_type
    return StopType.OTHER


def _estimate_duration(stop_type: StopType) -> int:
    """Estimate suggested visit duration in minutes."""
    durations = {
        StopType.SCENIC: 20,
        StopType.RESTAURANT: 45,
        StopType.CAFE: 20,
        StopType.GAS_STATION: 10,
        StopType.REST_AREA: 15,
        StopType.ATTRACTION: 60,
        StopType.BEACH: 45,
        StopType.PARK: 30,
        StopType.MUSEUM: 60,
        StopType.VIEWPOINT: 15,
        StopType.OTHER: 30,
    }
    return durations.get(stop_type, 30)


def _has_interest_coverage(
    selected: list[tuple[CandidateStop, StopScore]],
    preferences: UserPreferences,
) -> dict[str, bool]:
    """Check which interests are covered by selected stops."""
    coverage: dict[str, bool] = {interest: False for interest in preferences.interests}

    for candidate, _ in selected:
        for interest in preferences.interests:
            if coverage[interest]:
                continue
            interest_lower = interest.lower()
            if interest_lower in candidate.name.lower():
                coverage[interest] = True
                continue
            for t in candidate.types:
                if interest_lower in t.lower() or t.lower() in interest_lower:
                    coverage[interest] = True
                    break

    return coverage


def build_itinerary(
    ranked_candidates: list[tuple[CandidateStop, StopScore]],
    corridor: CorridorGeometry,
    preferences: UserPreferences,
    base_duration_s: float = 21600,
) -> list[Stop]:
    """
    Select stops from ranked candidates using a greedy forward pass.

    Constraints:
    - Stop interval: preferences.stop_interval_min to stop_interval_max minutes of driving
    - Meal windows: at least one food stop near meal fractions
    - Interest coverage: try to cover each interest with at least one stop
    - Detour budget: total detour <= 20% of route distance
    - ETA: total stop time + base_duration shouldn't exceed reasonable limits
    """
    if not ranked_candidates:
        return []

    total_distance = corridor.total_distance_m
    if total_distance <= 0:
        return []

    # Driving speed estimate: ~100 km/h
    avg_speed_ms = 100 * 1000 / 3600

    # Target stop spacing in meters
    min_spacing_m = preferences.stop_interval_min * 60 * avg_speed_ms
    max_spacing_m = preferences.stop_interval_max * 60 * avg_speed_ms

    # Detour budget: 20% of total route distance
    max_total_detour = total_distance * 0.20

    # Sort candidates by distance along route for forward pass
    sorted_candidates = sorted(ranked_candidates, key=lambda x: x[0].distance_along_route_m)

    selected: list[tuple[CandidateStop, StopScore]] = []
    last_stop_distance = 0.0
    total_detour = 0.0
    total_stop_time_s = 0.0
    meal_placed = False

    # Forward pass: greedily select stops
    for candidate, score in sorted_candidates:
        gap = candidate.distance_along_route_m - last_stop_distance

        # Skip if too close to last stop
        if gap < min_spacing_m and selected:
            continue

        # Skip if detour budget exhausted
        if total_detour + candidate.distance_to_route_m > max_total_detour:
            continue

        # Check if we need a meal stop
        route_fraction = candidate.distance_along_route_m / total_distance
        needs_meal = not meal_placed and 0.25 <= route_fraction <= 0.75
        is_food = bool(set(candidate.types) & RESTAURANT_TYPES)

        # Prefer adding a meal stop if we're in the meal window and haven't placed one
        if needs_meal and is_food:
            pass  # Always accept a meal stop in the window
        elif gap < min_spacing_m * 0.8:
            continue  # Too close even for a high-scoring stop
        elif score.total_score < 0.15:
            continue  # Score too low

        stop_type = _infer_stop_type(candidate.types)
        duration = _estimate_duration(stop_type)

        # Check total time budget
        if total_stop_time_s + duration * 60 > base_duration_s * 0.5:
            continue  # Stop time shouldn't exceed half the base driving time

        selected.append((candidate, score))
        last_stop_distance = candidate.distance_along_route_m
        total_detour += candidate.distance_to_route_m
        total_stop_time_s += duration * 60

        if is_food and 0.25 <= route_fraction <= 0.75:
            meal_placed = True

    # If no meal stop was placed, try to insert the best food candidate
    if not meal_placed:
        for candidate, score in sorted_candidates:
            is_food = bool(set(candidate.types) & RESTAURANT_TYPES)
            route_fraction = candidate.distance_along_route_m / total_distance
            if is_food and 0.2 <= route_fraction <= 0.8:
                # Check it doesn't violate spacing too badly
                can_insert = True
                for sel_c, _ in selected:
                    if abs(sel_c.distance_along_route_m - candidate.distance_along_route_m) < min_spacing_m * 0.5:
                        can_insert = False
                        break
                if can_insert:
                    selected.append((candidate, score))
                    selected.sort(key=lambda x: x[0].distance_along_route_m)
                    break

    # Convert to Stop objects
    stops = []
    for candidate, score in selected:
        stop_type = _infer_stop_type(candidate.types)
        stops.append(
            Stop(
                id=str(uuid.uuid4()),
                name=candidate.name,
                type=stop_type,
                lat=candidate.lat,
                lng=candidate.lng,
                place_id=candidate.place_id,
                suggested_duration_min=_estimate_duration(stop_type),
                distance_along_route_m=candidate.distance_along_route_m,
                detour_distance_m=candidate.distance_to_route_m,
                score=score,
            )
        )

    return stops
