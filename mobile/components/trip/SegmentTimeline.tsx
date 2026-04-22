import React from "react";
import { StyleSheet, View, Text, useColorScheme } from "react-native";
import type { Segment } from "../../types";

interface Props {
  segment: Segment;
}

export default function SegmentTimeline({ segment }: Props) {
  const isDark = useColorScheme() === "dark";
  const durationMin = Math.round(segment.duration_s / 60);
  const distKm = (segment.distance_m / 1000).toFixed(0);

  return (
    <View style={styles.container}>
      <View style={styles.line}>
        <View style={[styles.dot, isDark && styles.dotDark]} />
        <View style={[styles.connector, isDark && styles.connectorDark]} />
      </View>
      <View style={styles.content}>
        <Text style={[styles.driveText, isDark && styles.driveTextDark]}>
          Drive {distKm} km · {durationMin} min
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    paddingLeft: 4,
    marginBottom: 4,
  },
  line: {
    width: 28,
    alignItems: "center",
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: "#D1D5DB",
    marginBottom: 4,
  },
  dotDark: {
    backgroundColor: "#4B5563",
  },
  connector: {
    width: 2,
    flex: 1,
    backgroundColor: "#E5E7EB",
    minHeight: 16,
  },
  connectorDark: {
    backgroundColor: "#374151",
  },
  content: {
    flex: 1,
    paddingLeft: 8,
    justifyContent: "center",
    paddingBottom: 8,
  },
  driveText: {
    fontSize: 12,
    color: "#9CA3AF",
  },
  driveTextDark: {
    color: "#6B7280",
  },
});
