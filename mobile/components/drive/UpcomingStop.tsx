import React, { useEffect, useRef } from "react";
import { StyleSheet, View, Text, Animated, useColorScheme } from "react-native";
import type { Stop } from "../../types";

interface Props {
  stop: Stop;
  distanceM: number;
  visible: boolean;
}

export default function UpcomingStop({ stop, distanceM, visible }: Props) {
  const isDark = useColorScheme() === "dark";
  const slideAnim = useRef(new Animated.Value(100)).current;

  useEffect(() => {
    Animated.spring(slideAnim, {
      toValue: visible ? 0 : 100,
      useNativeDriver: true,
      tension: 80,
      friction: 12,
    }).start();
  }, [visible, slideAnim]);

  const distText =
    distanceM >= 1000
      ? `${(distanceM / 1000).toFixed(1)} km`
      : `${Math.round(distanceM)} m`;

  return (
    <Animated.View
      style={[
        styles.container,
        isDark && styles.containerDark,
        { transform: [{ translateY: slideAnim }] },
      ]}
    >
      <View style={styles.indicator} />
      <View style={styles.content}>
        <Text style={[styles.label, isDark && styles.labelDark]}>
          Approaching
        </Text>
        <Text style={[styles.name, isDark && styles.nameDark]}>
          {stop.name}
        </Text>
        <View style={styles.detailRow}>
          <Text style={styles.type}>{stop.type}</Text>
          <Text style={styles.distance}>{distText} away</Text>
          <Text style={styles.duration}>
            {stop.suggested_duration_min} min stop
          </Text>
        </View>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 16,
    marginHorizontal: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 6,
  },
  containerDark: {
    backgroundColor: "#1F2937",
  },
  indicator: {
    width: 36,
    height: 4,
    borderRadius: 2,
    backgroundColor: "#D1D5DB",
    alignSelf: "center",
    marginBottom: 12,
  },
  content: {},
  label: {
    fontSize: 11,
    fontWeight: "600",
    color: "#4F46E5",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  labelDark: {
    color: "#818CF8",
  },
  name: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 8,
  },
  nameDark: {
    color: "#F9FAFB",
  },
  detailRow: {
    flexDirection: "row",
    gap: 12,
  },
  type: {
    fontSize: 12,
    color: "#6B7280",
    textTransform: "capitalize",
  },
  distance: {
    fontSize: 12,
    color: "#4F46E5",
    fontWeight: "600",
  },
  duration: {
    fontSize: 12,
    color: "#6B7280",
  },
});
