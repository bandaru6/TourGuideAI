from enum import Enum
from pydantic import BaseModel, Field
import uuid

from .scoring import StopScore
from .corridor import CorridorGeometry
from .drive_events import TripState
from .preferences import UserPreferences


class StopType(str, Enum):
    SCENIC = "scenic"
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    GAS_STATION = "gas_station"
    REST_AREA = "rest_area"
    ATTRACTION = "attraction"
    BEACH = "beach"
    PARK = "park"
    MUSEUM = "museum"
    VIEWPOINT = "viewpoint"
    OTHER = "other"


class FunFact(BaseModel):
    text: str
    trigger_lat: float | None = None
    trigger_lng: float | None = None
    trigger_distance_along_route_m: float | None = None
    radius_m: float = 2000.0


class CandidateStop(BaseModel):
    place_id: str
    name: str
    lat: float
    lng: float
    types: list[str] = []
    rating: float | None = None
    price_level: int | None = None
    distance_to_route_m: float = 0.0
    distance_along_route_m: float = 0.0
    nearest_corridor_point_idx: int = 0


class Stop(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: StopType = StopType.OTHER
    lat: float
    lng: float
    place_id: str | None = None
    description: str = ""
    photos: list[str] = []
    suggested_duration_min: int = 30
    distance_along_route_m: float = 0.0
    detour_distance_m: float = 0.0
    score: StopScore | None = None
    fun_facts: list[FunFact] = []


class Segment(BaseModel):
    from_name: str
    to_name: str
    polyline: str = ""
    distance_m: float = 0.0
    duration_s: float = 0.0


class Trip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    origin: str
    destination: str
    preferences: UserPreferences = UserPreferences()
    state: TripState = TripState.DRAFT
    stops: list[Stop] = []
    segments: list[Segment] = []
    corridor: CorridorGeometry | None = None
    total_distance_m: float = 0.0
    total_duration_s: float = 0.0
    route_polyline: str = ""
    departure_time: str | None = None
