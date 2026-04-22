from app.models.corridor import CorridorGeometry
from app.models.preferences import UserPreferences
from app.models.scoring import RankingWeights, StopScore
from app.models.trip import CandidateStop

# Google Places types → categories for preference matching
SCENIC_TYPES = {"natural_feature", "park", "point_of_interest", "tourist_attraction", "beach"}
RESTAURANT_TYPES = {"restaurant", "cafe", "bakery", "bar", "meal_delivery", "meal_takeaway", "food"}
CULTURE_TYPES = {"museum", "art_gallery", "church", "hindu_temple", "mosque", "synagogue", "library"}
OUTDOOR_TYPES = {"park", "campground", "rv_park", "stadium", "amusement_park", "zoo", "aquarium"}

CATEGORY_MAP = {
    "scenic": SCENIC_TYPES,
    "food": RESTAURANT_TYPES,
    "culture": CULTURE_TYPES,
    "outdoor": OUTDOOR_TYPES,
    "beach": {"beach"},
    "nature": {"natural_feature", "park"},
    "history": {"museum", "church", "hindu_temple", "mosque", "synagogue"},
    "shopping": {"shopping_mall", "store", "clothing_store", "book_store"},
}


def _preference_match_score(candidate: CandidateStop, preferences: UserPreferences) -> float:
    """Score 0-1 based on how well the candidate matches user interests."""
    if not preferences.interests:
        return 0.5

    candidate_types = set(candidate.types)
    max_match = 0.0

    for interest in preferences.interests:
        interest_lower = interest.lower()
        # Check category map
        for category, types in CATEGORY_MAP.items():
            if category in interest_lower or interest_lower in category:
                overlap = len(candidate_types & types)
                if overlap > 0:
                    max_match = max(max_match, min(1.0, overlap / 2))

        # Check if interest keywords appear in candidate name
        if interest_lower in candidate.name.lower():
            max_match = max(max_match, 0.9)

    # Penalize avoided types
    for avoid in preferences.avoid_types:
        if avoid.lower() in " ".join(candidate.types).lower():
            return 0.0

    return max_match


def _scenic_value_score(candidate: CandidateStop) -> float:
    """Score 0-1 based on scenic potential."""
    candidate_types = set(candidate.types)
    scenic_overlap = len(candidate_types & SCENIC_TYPES)

    score = min(1.0, scenic_overlap * 0.3)

    # Boost based on rating
    if candidate.rating and candidate.rating >= 4.5:
        score = min(1.0, score + 0.3)
    elif candidate.rating and candidate.rating >= 4.0:
        score = min(1.0, score + 0.15)

    return score


def _meal_fit_score(
    candidate: CandidateStop,
    corridor: CorridorGeometry,
    preferences: UserPreferences,
    base_duration_s: float,
) -> float:
    """Score 0-1 based on whether this is a good meal stop near a meal time window."""
    candidate_types = set(candidate.types)
    is_food = len(candidate_types & RESTAURANT_TYPES) > 0

    if not is_food:
        return 0.0

    # Estimate arrival time fraction along route
    if corridor.total_distance_m > 0:
        route_fraction = candidate.distance_along_route_m / corridor.total_distance_m
    else:
        route_fraction = 0.5

    # Check proximity to meal windows (normalized to route fraction)
    # Assuming meal times are roughly at 1/3 and 2/3 of a typical day trip
    meal_fractions = [0.33, 0.67]
    min_gap = min(abs(route_fraction - mf) for mf in meal_fractions)

    # Score: closer to meal window = higher score
    if min_gap < 0.1:
        return 1.0
    elif min_gap < 0.2:
        return 0.7
    elif min_gap < 0.3:
        return 0.4
    return 0.1


def _timing_fit_score(
    candidate: CandidateStop,
    corridor: CorridorGeometry,
    preferences: UserPreferences,
) -> float:
    """Score 0-1 based on spacing from other stops (evaluated during itinerary construction)."""
    # This is a placeholder — real timing fit is evaluated in itinerary.py
    # Here we give a baseline based on route position
    if corridor.total_distance_m <= 0:
        return 0.5

    frac = candidate.distance_along_route_m / corridor.total_distance_m
    # Slightly prefer stops in the middle of the route (better spacing potential)
    if 0.15 <= frac <= 0.85:
        return 0.7
    return 0.4


def _detour_penalty_score(candidate: CandidateStop, corridor: CorridorGeometry) -> float:
    """Score 0-1 where 1.0 = no detour, 0.0 = max detour penalty."""
    if corridor.corridor_width_m <= 0:
        return 1.0

    ratio = candidate.distance_to_route_m / corridor.corridor_width_m
    return max(0.0, 1.0 - ratio)


def score_candidate(
    candidate: CandidateStop,
    preferences: UserPreferences,
    corridor: CorridorGeometry,
    base_duration_s: float = 21600,  # 6 hours default
    weights: RankingWeights | None = None,
) -> StopScore:
    """Compute a composite score for a candidate stop."""
    w = weights or RankingWeights()

    pref = _preference_match_score(candidate, preferences)
    scenic = _scenic_value_score(candidate)
    meal = _meal_fit_score(candidate, corridor, preferences, base_duration_s)
    timing = _timing_fit_score(candidate, corridor, preferences)
    detour = _detour_penalty_score(candidate, corridor)
    congestion = 0.0  # stubbed for MVP

    total = (
        w.preference * pref
        + w.scenic * scenic
        + w.meal * meal
        + w.timing * timing
        + w.detour * detour
        + w.congestion * (1.0 - congestion)
    )

    reason = generate_selection_reason(
        candidate, pref, scenic, meal, timing, detour
    )

    return StopScore(
        preference_match=round(pref, 3),
        scenic_value=round(scenic, 3),
        meal_fit=round(meal, 3),
        timing_fit=round(timing, 3),
        detour_penalty=round(1.0 - detour, 3),
        congestion_penalty=congestion,
        total_score=round(total, 3),
        selection_reason=reason,
        weights=w,
    )


def rank_candidates(
    candidates: list[CandidateStop],
    preferences: UserPreferences,
    corridor: CorridorGeometry,
    base_duration_s: float = 21600,
    weights: RankingWeights | None = None,
) -> list[tuple[CandidateStop, StopScore]]:
    """Score and rank all candidates, returning sorted by total_score descending."""
    scored = [
        (c, score_candidate(c, preferences, corridor, base_duration_s, weights))
        for c in candidates
    ]
    scored.sort(key=lambda x: x[1].total_score, reverse=True)
    return scored


def generate_selection_reason(
    candidate: CandidateStop,
    pref_score: float,
    scenic_score: float,
    meal_score: float,
    timing_score: float,
    detour_score: float,
) -> str:
    """Generate a human-readable explanation for why this stop was selected."""
    parts = []

    if pref_score >= 0.7:
        parts.append("strongly matches your interests")
    elif pref_score >= 0.4:
        parts.append("matches your interests")

    if scenic_score >= 0.6:
        parts.append("high scenic value")

    if meal_score >= 0.7:
        parts.append("great meal stop timing")
    elif meal_score >= 0.4:
        parts.append("near a meal window")

    if detour_score >= 0.9:
        detour_km = candidate.distance_to_route_m / 1000
        parts.append(f"only {detour_km:.1f}km off route")
    elif detour_score >= 0.7:
        detour_km = candidate.distance_to_route_m / 1000
        parts.append(f"{detour_km:.1f}km off route")

    if candidate.rating and candidate.rating >= 4.5:
        parts.append(f"rated {candidate.rating}/5")

    if not parts:
        parts.append("well-positioned along route")

    name = candidate.name
    return f"{name}: {', '.join(parts)}"
