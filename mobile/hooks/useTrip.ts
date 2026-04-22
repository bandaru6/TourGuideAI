import { useState, useEffect, useCallback, useRef } from "react";
import { getTrip, getDemoTrip } from "../services/api";
import type { Trip } from "../types";

const MAX_POLL_ATTEMPTS = 60; // 2s * 60 = 2 min max
const POLL_INTERVAL = 2000;

export function useTrip(tripId: string | undefined) {
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollCount = useRef(0);

  const fetchTrip = useCallback(async () => {
    if (!tripId) return;

    try {
      const t =
        tripId === "demo" ? await getDemoTrip() : await getTrip(tripId);
      setTrip(t);
      setError(null);

      if (t.state === "generating") {
        pollCount.current += 1;
        if (pollCount.current >= MAX_POLL_ATTEMPTS) {
          setError(
            "Trip generation is taking too long. Please try again."
          );
          return;
        }
        timeoutRef.current = setTimeout(fetchTrip, POLL_INTERVAL);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load trip"
      );
    } finally {
      setLoading(false);
    }
  }, [tripId]);

  useEffect(() => {
    pollCount.current = 0;
    setLoading(true);
    setError(null);
    fetchTrip();
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [fetchTrip]);

  const refresh = useCallback(() => {
    pollCount.current = 0;
    setLoading(true);
    setError(null);
    fetchTrip();
  }, [fetchTrip]);

  return { trip, loading, error, refresh };
}
