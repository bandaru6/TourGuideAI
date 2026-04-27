"""
Real-time rerouting service.

Handles full re-planning from current GPS position and lightweight
skip-and-replan operations.
"""

import logging

from app.engine.clustering import cluster_candidates, deduplicate_by_name
from app.engine.constraint_solver import ConstraintSolver
from app.engine.corridor import build_corridor
from app.engine.itinerary import build_itinerary
from app.engine.ranking import rank_candidates
from app.engine.traffic import apply_traffic_to_segments
from app.models.trip import Segment, Trip
from app.services.maps_service import MapsService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


class RerouteService:
    def __init__(self, maps: MapsService, gemini: GeminiService | None = None):
        self.maps = maps
        self.gemini = gemini

    async def reroute_from_position(
        self,
        trip: Trip,
        lat: float,
        lng: float,
        visited_stop_ids: list[str],
    ) -> Trip:
        """
        Full re-plan from current GPS to destination.
        Runs the complete pipeline: corridor -> cluster -> rank -> solve -> segments -> enrich.
        """
        # Get route from current position to destination
        route = await self.maps.get_route_from_coords(lat, lng, trip.destination)
        trip.route_polyline = route["polyline"]
        trip.total_distance_m = route["distance_m"]
        trip.total_duration_s = route["duration_s"]

        # Build new corridor
        corridor = build_corridor(route["polyline"])
        trip.corridor = corridor

        # Search candidates
        candidates = await self.maps.search_places_along_corridor(corridor)

        # Cluster & deduplicate
        candidates = deduplicate_by_name(candidates)
        candidates = cluster_candidates(candidates)

        # Rank
        ranked = rank_candidates(
            candidates,
            trip.preferences,
            corridor,
            base_duration_s=route["duration_s"],
        )

        # Solve with constraints
        solver = ConstraintSolver(
            ranked, corridor, trip.preferences,
            base_duration_s=route["duration_s"],
        )
        stops = solver.solve()

        # Fallback to greedy if solver returns empty
        if not stops:
            stops = build_itinerary(
                ranked, corridor, trip.preferences,
                base_duration_s=route["duration_s"],
            )

        # Remove any visited stops
        stops = [s for s in stops if s.id not in visited_stop_ids]
        trip.stops = stops

        # Rebuild segments
        await self._rebuild_segments(trip)

        # Apply traffic
        apply_traffic_to_segments(trip.segments)

        # Enrich if gemini available
        if self.gemini:
            try:
                trip = await self.gemini.enrich_trip(trip)
            except Exception as e:
                logger.warning(f"Enrichment failed during reroute: {e}")

        return trip

    async def handle_skip_and_replan(
        self,
        trip: Trip,
        skipped_stop_id: str,
        lat: float,
        lng: float,
        visited_stop_ids: list[str],
    ) -> Trip:
        """
        Lightweight replan: remove skipped stop, rebuild segments.
        """
        # Remove the skipped stop
        trip.stops = [s for s in trip.stops if s.id != skipped_stop_id]

        # Remove visited stops
        trip.stops = [s for s in trip.stops if s.id not in visited_stop_ids]

        # Rebuild segments
        await self._rebuild_segments(trip)

        # Apply traffic
        apply_traffic_to_segments(trip.segments)

        return trip

    async def _rebuild_segments(self, trip: Trip) -> None:
        """Rebuild route segments through remaining stops."""
        if trip.stops:
            waypoints = [{"lat": s.lat, "lng": s.lng} for s in trip.stops]
            segments_data = await self.maps.get_route_with_waypoints(
                trip.origin, trip.destination, waypoints
            )
            names = [trip.origin] + [s.name for s in trip.stops] + [trip.destination]
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
            route = await self.maps.get_route(trip.origin, trip.destination)
            trip.segments = [
                Segment(
                    from_name=trip.origin,
                    to_name=trip.destination,
                    polyline=route["polyline"],
                    distance_m=route["distance_m"],
                    duration_s=route["duration_s"],
                )
            ]
