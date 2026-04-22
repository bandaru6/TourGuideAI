export interface UserPreferences {
  interests: string[];
  avoid_types: string[];
  max_detour_min: number;
  meal_times: string[];
  stop_interval_min: number;
  stop_interval_max: number;
  scenic_priority: number;
  free_text: string;
}

export interface StopScore {
  preference_match: number;
  scenic_value: number;
  meal_fit: number;
  timing_fit: number;
  detour_penalty: number;
  congestion_penalty: number;
  total_score: number;
  selection_reason: string;
}

export interface FunFact {
  text: string;
  trigger_lat: number | null;
  trigger_lng: number | null;
  trigger_distance_along_route_m: number | null;
  radius_m: number;
}

export interface Stop {
  id: string;
  name: string;
  type: string;
  lat: number;
  lng: number;
  place_id: string | null;
  description: string;
  photos: string[];
  suggested_duration_min: number;
  distance_along_route_m: number;
  detour_distance_m: number;
  score: StopScore | null;
  fun_facts: FunFact[];
}

export interface Segment {
  from_name: string;
  to_name: string;
  polyline: string;
  distance_m: number;
  duration_s: number;
}

export interface CorridorPoint {
  lat: number;
  lng: number;
  distance_along_route_m: number;
  bearing: number;
}

export interface CorridorGeometry {
  route_polyline: string;
  sample_points: CorridorPoint[];
  corridor_width_m: number;
  total_distance_m: number;
}

export type TripState =
  | "draft"
  | "generating"
  | "ready"
  | "active"
  | "approaching_stop"
  | "at_stop"
  | "resumed"
  | "rerouting"
  | "completed";

export interface Trip {
  id: string;
  origin: string;
  destination: string;
  preferences: UserPreferences;
  state: TripState;
  stops: Stop[];
  segments: Segment[];
  corridor: CorridorGeometry | null;
  total_distance_m: number;
  total_duration_s: number;
  route_polyline: string;
  departure_time: string | null;
}

export interface DriveEvent {
  type: string;
  stop_id: string | null;
  message: string;
  data: Record<string, unknown>;
  lat: number | null;
  lng: number | null;
}

export interface CreateTripRequest {
  origin: string;
  destination: string;
  preferences?: Partial<UserPreferences>;
  departure_time?: string;
}
