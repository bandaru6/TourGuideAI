import Constants from "expo-constants";
import type { Trip, Stop, CreateTripRequest } from "../types";

const API_BASE =
  Constants.expoConfig?.extra?.apiUrl || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    // Try to parse structured error from backend
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (body.detail?.message) {
        message = body.detail.message;
      } else if (body.message) {
        message = body.message;
      }
    } catch {
      const text = await res.text().catch(() => "");
      if (text) message = text;
    }
    throw new Error(message);
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

export function listTrips(): Promise<Trip[]> {
  return request<Trip[]>("/api/trips");
}

export function startTrip(
  tripId: string
): Promise<{ status: string; ws_url: string }> {
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

export function getWsUrl(tripId: string): string {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/ws/drive/${tripId}`;
}
