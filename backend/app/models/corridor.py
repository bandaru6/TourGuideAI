from pydantic import BaseModel


class CorridorPoint(BaseModel):
    lat: float
    lng: float
    distance_along_route_m: float
    bearing: float


class CorridorGeometry(BaseModel):
    route_polyline: str
    sample_points: list[CorridorPoint]
    corridor_width_m: float
    total_distance_m: float
