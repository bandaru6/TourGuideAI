import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getTrip, getDemoTrip } from "../services/api";
import type { Trip } from "../types";

export default function TripReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    if (id === "demo") {
      getDemoTrip()
        .then((t) => setTrip(t))
        .catch(() => setError("Failed to load demo trip"));
      return;
    }

    const poll = async () => {
      try {
        const t = await getTrip(id);
        setTrip(t);
        if (t.state === "generating") {
          setTimeout(poll, 2000);
        }
      } catch {
        setError("Failed to load trip");
      }
    };
    poll();
  }, [id]);

  if (error) return <div style={{ padding: 40 }}>{error}</div>;
  if (!trip) return <div style={{ padding: 40 }}>Loading...</div>;

  if (trip.state === "generating") {
    return (
      <div style={{ padding: 40, textAlign: "center" }}>
        <h2>Generating your trip...</h2>
        <p>Finding the best stops along your route.</p>
      </div>
    );
  }

  if (trip.state === "draft" && trip.stops.length === 0 && trip.total_distance_m === 0) {
    return (
      <div style={{ padding: 40, textAlign: "center" }}>
        <h2>Trip generation failed</h2>
        <p>Could not generate this trip. Please try again or use the demo.</p>
        <a href="/trip/demo" style={{ color: "#2563eb" }}>Try Demo Trip (SF → LA)</a>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 40 }}>
      <h1>
        {trip.origin} → {trip.destination}
      </h1>
      <p>
        {(trip.total_distance_m / 1000).toFixed(0)} km |{" "}
        {(trip.total_duration_s / 3600).toFixed(1)} hours | {trip.stops.length}{" "}
        stops
      </p>

      <h2>Stops</h2>
      {trip.stops.map((stop) => (
        <div
          key={stop.id}
          style={{
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 16,
            marginBottom: 12,
          }}
        >
          <h3>{stop.name}</h3>
          <p style={{ color: "#666", fontSize: 14 }}>
            {stop.type} | {stop.suggested_duration_min} min |{" "}
            {(stop.detour_distance_m / 1000).toFixed(1)} km detour
          </p>
          {stop.score && (
            <div style={{ fontSize: 13, color: "#888" }}>
              <strong>Score:</strong> {stop.score.total_score.toFixed(2)} |{" "}
              {stop.score.selection_reason}
            </div>
          )}
        </div>
      ))}

      {trip.state === "ready" && (
        <button
          onClick={() => navigate(`/drive/${trip.id}`)}
          style={{ padding: "10px 24px", fontSize: 16, marginTop: 16 }}
        >
          Start Drive
        </button>
      )}
    </div>
  );
}
