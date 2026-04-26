import type { Trip, Stop, CreateTripRequest } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export function createTrip(data: CreateTripRequest): Promise<Trip> {
  return request<Trip>("/api/trips", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getTrip(id: string): Promise<Trip> {
  return request<Trip>(`/api/trips/${id}`);
}

export function getStops(tripId: string): Promise<Stop[]> {
  return request<Stop[]>(`/api/trips/${tripId}/stops`);
}

export function startTrip(tripId: string): Promise<{ status: string; ws_url: string }> {
  return request(`/api/trips/${tripId}/start`, { method: "POST" });
}

export function skipStop(
  tripId: string,
  stopId: string
): Promise<{ status: string; remaining_stops: number }> {
  return request(`/api/trips/${tripId}/skip-stop/${stopId}`, {
    method: "POST",
  });
}

export function getDemoTrip(): Promise<Trip> {
  return request<Trip>("/api/demo/sf-to-la");
}
