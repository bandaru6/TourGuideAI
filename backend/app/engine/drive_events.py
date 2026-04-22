from app.engine.geo_utils import haversine
from app.engine.corridor import is_within_corridor
from app.models.corridor import CorridorGeometry
from app.models.drive_events import DriveEvent, DriveEventType
from app.models.trip import Stop, Trip


class DriveEventEngine:
    """
    Processes GPS location updates against trip state to generate drive events.
    Tracks already-triggered events to prevent duplicates.
    """

    APPROACH_RADIUS_M = 2000
    ARRIVAL_RADIUS_M = 200
    OFF_CORRIDOR_THRESHOLD_M = 5000

    def __init__(self, trip: Trip):
        self.trip = trip
        self.remaining_stops = list(trip.stops)
        self.corridor = trip.corridor
        self.triggered_stop_ids: set[str] = set()
        self.triggered_fun_fact_indices: set[int] = set()
        self.current_segment_idx = 0
        self.off_corridor_count = 0

    def process_location(
        self, lat: float, lng: float, speed: float = 0.0, heading: float = 0.0
    ) -> list[DriveEvent]:
        events: list[DriveEvent] = []

        # Check stop proximity
        for stop in self.remaining_stops:
            dist = haversine(lat, lng, stop.lat, stop.lng)

            if dist <= self.ARRIVAL_RADIUS_M and stop.id not in self.triggered_stop_ids:
                self.triggered_stop_ids.add(stop.id)
                events.append(
                    DriveEvent(
                        type=DriveEventType.ENTERED_REGION,
                        stop_id=stop.id,
                        message=f"You've arrived at {stop.name}",
                        lat=lat,
                        lng=lng,
                    )
                )
            elif dist <= self.APPROACH_RADIUS_M and f"approach_{stop.id}" not in self.triggered_stop_ids:
                self.triggered_stop_ids.add(f"approach_{stop.id}")
                events.append(
                    DriveEvent(
                        type=DriveEventType.APPROACHING_STOP,
                        stop_id=stop.id,
                        message=f"{stop.name} is {dist/1000:.1f}km ahead",
                        lat=lat,
                        lng=lng,
                        data={"distance_m": dist},
                    )
                )

        # Check fun fact triggers
        for i, stop in enumerate(self.trip.stops):
            for j, fact in enumerate(stop.fun_facts):
                fact_key = f"fact_{i}_{j}"
                if fact_key in self.triggered_fun_fact_indices:
                    continue
                if fact.trigger_lat is not None and fact.trigger_lng is not None:
                    dist = haversine(lat, lng, fact.trigger_lat, fact.trigger_lng)
                    if dist <= fact.radius_m:
                        self.triggered_fun_fact_indices.add(fact_key)
                        events.append(
                            DriveEvent(
                                type=DriveEventType.NARRATION_TRIGGER,
                                message=fact.text,
                                lat=lat,
                                lng=lng,
                            )
                        )

        # Check missed stops
        for stop in list(self.remaining_stops):
            if stop.id in self.triggered_stop_ids:
                continue
            # If we've passed the stop's route position significantly
            if self.corridor and self.corridor.total_distance_m > 0:
                from app.engine.geo_utils import distance_along_polyline, decode_polyline

                polyline_points = decode_polyline(self.corridor.route_polyline)
                current_along, _ = distance_along_polyline(lat, lng, polyline_points)
                if current_along > stop.distance_along_route_m + self.APPROACH_RADIUS_M * 2:
                    miss_key = f"missed_{stop.id}"
                    if miss_key not in self.triggered_stop_ids:
                        self.triggered_stop_ids.add(miss_key)
                        events.append(
                            DriveEvent(
                                type=DriveEventType.MISSED_STOP,
                                stop_id=stop.id,
                                message=f"You've passed {stop.name}",
                                lat=lat,
                                lng=lng,
                            )
                        )

        # Check off-corridor
        if self.corridor and not is_within_corridor(lat, lng, self.corridor):
            self.off_corridor_count += 1
            if self.off_corridor_count >= 3:  # ~60s at 20s intervals
                events.append(
                    DriveEvent(
                        type=DriveEventType.REROUTE_NEEDED,
                        message="You appear to be off the planned route",
                        lat=lat,
                        lng=lng,
                    )
                )
                self.off_corridor_count = 0
        else:
            self.off_corridor_count = 0

        return events
