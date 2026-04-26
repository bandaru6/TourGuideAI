import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { createTrip } from "../services/api";

export default function TripPlanner() {
  const navigate = useNavigate();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [interests, setInterests] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const trip = await createTrip({
        origin,
        destination,
        preferences: {
          interests: interests
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
        },
      });
      navigate(`/trip/${trip.id}`);
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Failed to create trip";
      setError(msg);
      console.error("Failed to create trip:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: 40 }}>
      <h1>TourGuideAI</h1>
      <p>Plan your road trip with intelligent stop selection.</p>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label>
            Origin
            <input
              type="text"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="San Francisco, CA"
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
              required
            />
          </label>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label>
            Destination
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Los Angeles, CA"
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
              required
            />
          </label>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label>
            Interests (comma-separated)
            <input
              type="text"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
              placeholder="scenic, beach, food, nature"
              style={{ display: "block", width: "100%", padding: 8, marginTop: 4 }}
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={loading}
          style={{ padding: "10px 24px", fontSize: 16 }}
        >
          {loading ? "Planning..." : "Plan Trip"}
        </button>
      </form>

      {error && (
        <div
          style={{
            marginTop: 20,
            padding: 16,
            background: "#fef2f2",
            border: "1px solid #fca5a5",
            borderRadius: 8,
            color: "#991b1b",
          }}
        >
          <p style={{ margin: 0 }}>{error}</p>
          <Link
            to="/trip/demo"
            style={{
              display: "inline-block",
              marginTop: 8,
              color: "#2563eb",
              textDecoration: "underline",
            }}
          >
            Try Demo Trip (SF → LA)
          </Link>
        </div>
      )}
    </div>
  );
}
