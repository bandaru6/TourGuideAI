import { useState, useEffect, useRef, useCallback } from "react";
import { getWsUrl } from "../services/api";
import type { DriveEvent } from "../types";

interface DriveSocketState {
  connected: boolean;
  events: DriveEvent[];
  lastEvent: DriveEvent | null;
  error: string | null;
}

const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_RECONNECT_DELAY = 1000;

export function useDriveSocket(tripId: string | undefined, active: boolean) {
  const [state, setState] = useState<DriveSocketState>({
    connected: false,
    events: [],
    lastEvent: null,
    error: null,
  });
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activeRef = useRef(active);
  activeRef.current = active;

  const connect = useCallback(() => {
    if (!tripId || !activeRef.current) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(getWsUrl(tripId));
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttempts.current = 0;
      setState((s) => ({ ...s, connected: true, error: null }));
    };

    ws.onmessage = (e) => {
      try {
        const event: DriveEvent = JSON.parse(e.data);
        // Skip ack messages from event list
        if (event.type === "position_ack") return;
        setState((s) => ({
          ...s,
          events: [...s.events, event],
          lastEvent: event,
        }));
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      setState((s) => ({ ...s, error: "Connection error" }));
    };

    ws.onclose = () => {
      setState((s) => ({ ...s, connected: false }));
      wsRef.current = null;

      // Auto-reconnect with exponential backoff
      if (activeRef.current && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current);
        reconnectAttempts.current += 1;
        reconnectTimer.current = setTimeout(connect, delay);
      } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
        setState((s) => ({
          ...s,
          error: "Connection lost. Please restart the simulation.",
        }));
      }
    };
  }, [tripId]);

  useEffect(() => {
    if (active) {
      reconnectAttempts.current = 0;
      connect();
    }

    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [tripId, active, connect]);

  const sendLocation = useCallback(
    (lat: number, lng: number, speed: number = 0, heading: number = 0) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ lat, lng, speed, heading, simulated: false })
        );
      }
    },
    []
  );

  const sendSimulated = useCallback(
    (lat: number, lng: number) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ lat, lng, speed: 0, heading: 0, simulated: true })
        );
      }
    },
    []
  );

  return { ...state, sendLocation, sendSimulated };
}
