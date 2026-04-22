import React from "react";
import { StyleSheet, View, Text, useColorScheme } from "react-native";
import type { Stop } from "../../types";

interface Props {
  stop: Stop;
  index: number;
}

const TYPE_BADGES: Record<string, { label: string; bg: string; fg: string }> = {
  scenic: { label: "Scenic", bg: "#D1FAE5", fg: "#065F46" },
  viewpoint: { label: "Viewpoint", bg: "#D1FAE5", fg: "#065F46" },
  beach: { label: "Beach", bg: "#CFFAFE", fg: "#155E75" },
  park: { label: "Park", bg: "#D1FAE5", fg: "#065F46" },
  restaurant: { label: "Restaurant", bg: "#FEF3C7", fg: "#92400E" },
  cafe: { label: "Cafe", bg: "#FEF3C7", fg: "#92400E" },
  attraction: { label: "Attraction", bg: "#E0E7FF", fg: "#3730A3" },
  museum: { label: "Museum", bg: "#EDE9FE", fg: "#5B21B6" },
  gas_station: { label: "Gas", bg: "#F3F4F6", fg: "#374151" },
  rest_area: { label: "Rest", bg: "#F3F4F6", fg: "#374151" },
};

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <View style={barStyles.row}>
      <Text style={barStyles.label}>{label}</Text>
      <View style={barStyles.track}>
        <View
          style={[
            barStyles.fill,
            { width: `${Math.max(2, value * 100)}%` },
          ]}
        />
      </View>
      <Text style={barStyles.value}>{value.toFixed(2)}</Text>
    </View>
  );
}

export default function StopCard({ stop, index }: Props) {
  const isDark = useColorScheme() === "dark";
  const badge = TYPE_BADGES[stop.type.toLowerCase()] || {
    label: stop.type,
    bg: "#F3F4F6",
    fg: "#374151",
  };

  return (
    <View
      style={[
        styles.card,
        isDark && styles.cardDark,
      ]}
    >
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={[styles.index, isDark && styles.textDark]}>
            {index + 1}
          </Text>
          <View style={{ flex: 1 }}>
            <Text style={[styles.name, isDark && styles.textDark]}>
              {stop.name}
            </Text>
            <View style={styles.metaRow}>
              <View style={[styles.badge, { backgroundColor: badge.bg }]}>
                <Text style={[styles.badgeText, { color: badge.fg }]}>
                  {badge.label}
                </Text>
              </View>
              <Text style={styles.meta}>
                {stop.suggested_duration_min} min
              </Text>
              <Text style={styles.meta}>
                {(stop.detour_distance_m / 1000).toFixed(1)} km detour
              </Text>
            </View>
          </View>
        </View>
      </View>

      {stop.score != null && stop.score.total_score != null && (
        <View style={styles.scoreSection}>
          <ScoreBar label="Preference" value={stop.score.preference_match ?? 0} />
          <ScoreBar label="Scenic" value={stop.score.scenic_value ?? 0} />
          <ScoreBar label="Meal Fit" value={stop.score.meal_fit ?? 0} />
          <ScoreBar label="Timing" value={stop.score.timing_fit ?? 0} />
          <ScoreBar label="Detour" value={stop.score.detour_penalty ?? 0} />

          <Text style={styles.totalScore}>
            Score: {stop.score.total_score.toFixed(2)}
          </Text>
          {stop.score.selection_reason ? (
            <Text style={styles.reason}>{stop.score.selection_reason}</Text>
          ) : null}
        </View>
      )}

      {stop.description ? (
        <Text style={[styles.description, isDark && styles.textMutedDark]}>
          {stop.description}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  cardDark: {
    backgroundColor: "#1F2937",
  },
  header: {},
  titleRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
  },
  index: {
    fontSize: 20,
    fontWeight: "800",
    color: "#4F46E5",
    width: 28,
    textAlign: "center",
    marginTop: 2,
  },
  name: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 6,
  },
  textDark: {
    color: "#F9FAFB",
  },
  textMutedDark: {
    color: "#9CA3AF",
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flexWrap: "wrap",
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  meta: {
    fontSize: 12,
    color: "#6B7280",
  },
  scoreSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#F3F4F6",
  },
  totalScore: {
    fontSize: 13,
    fontWeight: "700",
    color: "#4F46E5",
    marginTop: 8,
  },
  reason: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 4,
    fontStyle: "italic",
  },
  description: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 8,
  },
});

const barStyles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  label: {
    fontSize: 11,
    color: "#6B7280",
    width: 68,
  },
  track: {
    flex: 1,
    height: 6,
    backgroundColor: "#F3F4F6",
    borderRadius: 3,
    marginHorizontal: 8,
    overflow: "hidden",
  },
  fill: {
    height: 6,
    backgroundColor: "#4F46E5",
    borderRadius: 3,
  },
  value: {
    fontSize: 11,
    color: "#9CA3AF",
    width: 32,
    textAlign: "right",
  },
});
