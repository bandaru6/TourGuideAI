import logging

from app.config import Settings
from app.db.store import TripStore
from app.engine.corridor import build_corridor
from app.engine.ranking import rank_candidates
from app.engine.itinerary import build_itinerary
from app.models.drive_events import TripState
from app.models.trip import Trip, Segment
from app.services.maps_service import MapsService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class TourAssembler:
    """
    Pipeline orchestrator for trip generation.

    Steps:
    1. ROUTE       → get_route() → polyline, distance, duration
    2. CORRIDOR    → build_corridor() → CorridorGeometry
    3. CANDIDATES  → search_places_along_corridor() → list[CandidateStop]
    4. RANKING     → rank_candidates() → scored candidates
    5. ITINERARY   → build_itinerary() → selected + ordered Stops
    6. SEGMENTS    → get_route_with_waypoints() → per-segment polylines
    7. ENRICHMENT  → Gemini fun facts + descriptions
    8. PLAYLISTS   → [Phase 6]
    9. ASSEMBLY    → Trip model, status → READY
    """

    def __init__(self, settings: Settings):
        self.maps = MapsService()
        self.gemini = GeminiService(settings.gemini_api_key)
        self.settings = settings

    async def generate_trip(self, trip: Trip, store: TripStore) -> Trip:
        try:
            # Step 1: Route
            logger.info(f"[{trip.id}] Step 1: Getting route {trip.origin} → {trip.destination}")
            route = await self.maps.get_route(trip.origin, trip.destination)
            trip.route_polyline = route["polyline"]
            trip.total_distance_m = route["distance_m"]
            trip.total_duration_s = route["duration_s"]

            # Step 2: Corridor
            logger.info(f"[{trip.id}] Step 2: Building corridor")
            corridor = build_corridor(route["polyline"])
            trip.corridor = corridor

            # Step 3: Candidates
            logger.info(f"[{trip.id}] Step 3: Searching for candidates")
            candidates = await self.maps.search_places_along_corridor(corridor)
            logger.info(f"[{trip.id}] Found {len(candidates)} candidates")

            # Step 4: Ranking
            logger.info(f"[{trip.id}] Step 4: Ranking candidates")
            ranked = rank_candidates(
                candidates,
                trip.preferences,
                corridor,
                base_duration_s=route["duration_s"],
            )

            # Step 5: Itinerary
            logger.info(f"[{trip.id}] Step 5: Building itinerary")
            stops = build_itinerary(
                ranked,
                corridor,
                trip.preferences,
                base_duration_s=route["duration_s"],
            )
            trip.stops = stops
            logger.info(f"[{trip.id}] Selected {len(stops)} stops")

            # Step 6: Segments
            if stops:
                logger.info(f"[{trip.id}] Step 6: Getting segments")
                waypoints = [{"lat": s.lat, "lng": s.lng} for s in stops]
                segments_data = await self.maps.get_route_with_waypoints(
                    trip.origin, trip.destination, waypoints
                )

                # Build segment names
                names = [trip.origin] + [s.name for s in stops] + [trip.destination]
                trip.segments = [
                    Segment(
                        from_name=names[i],
                        to_name=names[i + 1],
                        polyline=seg["polyline"],
                        distance_m=seg["distance_m"],
                        duration_s=seg["duration_s"],
                    )
                    for i, seg in enumerate(segments_data)
                ]
            else:
                trip.segments = [
                    Segment(
                        from_name=trip.origin,
                        to_name=trip.destination,
                        polyline=route["polyline"],
                        distance_m=route["distance_m"],
                        duration_s=route["duration_s"],
                    )
                ]

            # Step 7: Enrichment (Gemini — graceful degradation)
            logger.info(f"[{trip.id}] Step 7: Enriching with Gemini")
            trip = await self.gemini.enrich_trip(trip)

            trip.state = TripState.READY
            logger.info(f"[{trip.id}] Trip generation complete — READY")

        except Exception as e:
            logger.error(f"[{trip.id}] Trip generation failed: {e}", exc_info=True)
            trip.state = TripState.DRAFT  # Reset to draft on failure

        await store.save(trip)
        return trip
