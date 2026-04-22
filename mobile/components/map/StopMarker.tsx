import React from "react";
import { StyleSheet, View, Text } from "react-native";
import { Marker, Callout } from "react-native-maps";
import type { Stop } from "../../types";

interface Props {
  stop: Stop;
}

const TYPE_COLORS: Record<string, string> = {
  scenic: "#10B981",
  viewpoint: "#10B981",
  beach: "#06B6D4",
  park: "#10B981",
  restaurant: "#F59E0B",
  cafe: "#F59E0B",
  food: "#F59E0B",
  attraction: "#6366F1",
  museum: "#8B5CF6",
  gas_station: "#6B7280",
  rest_area: "#6B7280",
  other: "#6B7280",
};

function getMarkerColor(type: string): string {
  const lower = type.toLowerCase();
  return TYPE_COLORS[lower] || "#6366F1";
}

const TYPE_ICONS: Record<string, string> = {
  scenic: "🏔",
  viewpoint: "👁",
  beach: "🏖",
  park: "🌲",
  restaurant: "🍽",
  cafe: "☕",
  food: "🍽",
  attraction: "⭐",
  museum: "🏛",
  gas_station: "⛽",
  rest_area: "🅿️",
};

function getIcon(type: string): string {
  return TYPE_ICONS[type.toLowerCase()] || "📍";
}

export default function StopMarker({ stop }: Props) {
  const color = getMarkerColor(stop.type);

  return (
    <Marker
      coordinate={{ latitude: stop.lat, longitude: stop.lng }}
      title={stop.name}
      anchor={{ x: 0.5, y: 1 }}
    >
      <View style={[styles.marker, { backgroundColor: color }]}>
        <Text style={styles.icon}>{getIcon(stop.type)}</Text>
      </View>
      <Callout tooltip>
        <View style={styles.callout}>
          <Text style={styles.calloutTitle}>{stop.name}</Text>
          <Text style={styles.calloutType}>{stop.type}</Text>
          {stop.score && (
            <>
              <Text style={styles.calloutScore}>
                Score: {stop.score.total_score.toFixed(2)}
              </Text>
              <Text style={styles.calloutReason}>
                {stop.score.selection_reason}
              </Text>
            </>
          )}
          <Text style={styles.calloutDetail}>
            {stop.suggested_duration_min} min &middot;{" "}
            {(stop.detour_distance_m / 1000).toFixed(1)} km detour
          </Text>
        </View>
      </Callout>
    </Marker>
  );
}

const styles = StyleSheet.create({
  marker: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#fff",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 4,
  },
  icon: {
    fontSize: 14,
  },
  callout: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    minWidth: 180,
    maxWidth: 240,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  calloutTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 2,
  },
  calloutType: {
    fontSize: 11,
    color: "#6B7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  calloutScore: {
    fontSize: 12,
    fontWeight: "600",
    color: "#4F46E5",
    marginBottom: 2,
  },
  calloutReason: {
    fontSize: 11,
    color: "#374151",
    marginBottom: 4,
  },
  calloutDetail: {
    fontSize: 11,
    color: "#9CA3AF",
  },
});
