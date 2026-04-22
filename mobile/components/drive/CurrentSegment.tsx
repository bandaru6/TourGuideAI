import React from "react";
import { StyleSheet, View, Text, useColorScheme } from "react-native";
import type { Segment } from "../../types";

interface Props {
  segment: Segment | null;
  progress: number; // 0-1
}

export default function CurrentSegment({ segment, progress }: Props) {
  const isDark = useColorScheme() === "dark";

  if (!segment) return null;

  const remainingMin = Math.round(
    (segment.duration_s * (1 - progress)) / 60
  );
  const remainingKm = ((segment.distance_m * (1 - progress)) / 1000).toFixed(
    1
  );

  return (
    <View style={[styles.container, isDark && styles.containerDark]}>
      <View style={styles.header}>
        <Text style={[styles.label, isDark && styles.labelDark]}>
          Current Segment
        </Text>
        <Text style={[styles.eta, isDark && styles.etaDark]}>
          {remainingMin} min left
        </Text>
      </View>
      <Text style={[styles.route, isDark && styles.routeDark]}>
        {segment.from_name} → {segment.to_name}
      </Text>
      <View style={styles.progressTrack}>
        <View
          style={[styles.progressFill, { width: `${progress * 100}%` }]}
        />
      </View>
      <Text style={[styles.distance, isDark && styles.distanceDark]}>
        {remainingKm} km remaining
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  containerDark: {
    backgroundColor: "#1F2937",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  label: {
    fontSize: 11,
    fontWeight: "600",
    color: "#6B7280",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  labelDark: {
    color: "#9CA3AF",
  },
  eta: {
    fontSize: 14,
    fontWeight: "700",
    color: "#4F46E5",
  },
  etaDark: {
    color: "#818CF8",
  },
  route: {
    fontSize: 16,
    fontWeight: "600",
    color: "#1F2937",
    marginBottom: 8,
  },
  routeDark: {
    color: "#F9FAFB",
  },
  progressTrack: {
    height: 4,
    backgroundColor: "#E5E7EB",
    borderRadius: 2,
    marginBottom: 6,
    overflow: "hidden",
  },
  progressFill: {
    height: 4,
    backgroundColor: "#4F46E5",
    borderRadius: 2,
  },
  distance: {
    fontSize: 12,
    color: "#9CA3AF",
  },
  distanceDark: {
    color: "#6B7280",
  },
});
