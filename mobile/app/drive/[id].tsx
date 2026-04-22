import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  StyleSheet,
  View,
  Text,
  Pressable,
  SafeAreaView,
  useColorScheme,
  Animated,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTrip } from "../../hooks/useTrip";
import { useDriveSocket } from "../../hooks/useDriveSocket";
import { decodePolyline, interpolateAlongPolyline } from "../../services/polyline";
import DriveMap from "../../components/map/DriveMap";
import CurrentSegment from "../../components/drive/CurrentSegment";
import UpcomingStop from "../../components/drive/UpcomingStop";
import FunFactPopup from "../../components/drive/FunFactPopup";
import type { Stop, DriveEvent } from "../../types";

const SPEED_OPTIONS = [1, 2, 5, 10];

export default function DriveView() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const isDark = useColorScheme() === "dark";
  const mapRef = useRef<any>(null);
  const { trip } = useTrip(id);

  const [isSimulating, setIsSimulating] = useState(false);
  const [speedMultiplier, setSpeedMultiplier] = useState(2);
  const [progress, setProgress] = useState(0);
  const [carPosition, setCarPosition] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);

  const { connected, lastEvent, sendSimulated } = useDriveSocket(
    id,
    isSimulating
  );

  const [approachingStop, setApproachingStop] = useState<Stop | null>(null);
  const [approachDist, setApproachDist] = useState(0);
  const [funFactText, setFunFactText] = useState("");
  const [showFunFact, setShowFunFact] = useState(false);
  const [currentSegmentIdx, setCurrentSegmentIdx] = useState(0);
  const [toastMessage, setToastMessage] = useState("");
  const toastOpacity = useRef(new Animated.Value(0)).current;

  const routeCoords = React.useMemo(
    () => (trip?.route_polyline ? decodePolyline(trip.route_polyline) : []),
    [trip?.route_polyline]
  );

  // Handle drive events
  useEffect(() => {
    if (!lastEvent || !trip) return;
    const event: DriveEvent = lastEvent;

    switch (event.type) {
      case "approaching_stop": {
        const stop = trip.stops.find((s) => s.id === event.stop_id);
        if (stop) {
          setApproachingStop(stop);
          setApproachDist((event.data?.distance_m as number) || 2000);
        }
        break;
      }
      case "entered_region":
        setApproachingStop(null);
        showToast(event.message || "Arrived at stop");
        break;
      case "narration_trigger":
        setFunFactText(event.message);
        setShowFunFact(true);
        break;
      case "missed_stop":
        showToast(event.message || "Missed a stop");
        break;
      case "segment_changed":
        setCurrentSegmentIdx((i) => i + 1);
        break;
    }
  }, [lastEvent, trip]);

  const showToast = useCallback(
    (msg: string) => {
      setToastMessage(msg);
      Animated.sequence([
        Animated.timing(toastOpacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: false,
        }),
        Animated.delay(3000),
        Animated.timing(toastOpacity, {
          toValue: 0,
          duration: 300,
          useNativeDriver: false,
        }),
      ]).start();
    },
    [toastOpacity]
  );

  // Simulation loop
  useEffect(() => {
    if (!isSimulating || routeCoords.length === 0 || !trip) return;

    const totalDurationMs = (trip.total_duration_s * 1000) / speedMultiplier;
    const intervalMs = 100;
    const step = intervalMs / totalDurationMs;

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + step;
        if (next >= 1) {
          setIsSimulating(false);
          showToast("Trip completed!");
          return 1;
        }

        const pos = interpolateAlongPolyline(routeCoords, next);
        setCarPosition(pos);
        sendSimulated(pos.latitude, pos.longitude);

        if (mapRef.current?.animateCamera) {
          mapRef.current.animateCamera(
            { center: pos, zoom: 13 },
            { duration: 200 }
          );
        }

        return next;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isSimulating, speedMultiplier, routeCoords, trip, sendSimulated, showToast]);

  const handleStartSimulation = useCallback(() => {
    if (routeCoords.length === 0) return;
    setProgress(0);
    setCarPosition(routeCoords[0]);
    setIsSimulating(true);
  }, [routeCoords]);

  const handleStopSimulation = useCallback(() => {
    setIsSimulating(false);
  }, []);

  if (!trip) {
    return (
      <SafeAreaView style={[styles.flex, styles.center]}>
        <Text style={styles.loadingText}>Loading...</Text>
      </SafeAreaView>
    );
  }

  const currentSegment =
    trip.segments[currentSegmentIdx] || trip.segments[0] || null;

  const initialRegion =
    routeCoords.length > 0
      ? {
          latitude: routeCoords[0].latitude,
          longitude: routeCoords[0].longitude,
          latitudeDelta: 2,
          longitudeDelta: 2,
        }
      : undefined;

  return (
    <SafeAreaView style={[styles.flex, isDark && styles.bgDark]}>
      {/* Map */}
      <View style={styles.mapContainer}>
        <DriveMap
          ref={mapRef}
          trip={trip}
          carPosition={carPosition}
          initialRegion={initialRegion}
        />

        {/* Fun fact popup */}
        <FunFactPopup
          text={funFactText}
          visible={showFunFact}
          onDismiss={() => setShowFunFact(false)}
        />

        {/* Toast */}
        <Animated.View
          style={[styles.toast, { opacity: toastOpacity }]}
          pointerEvents="none"
        >
          <Text style={styles.toastText}>{toastMessage}</Text>
        </Animated.View>

        {/* Back button */}
        <Pressable
          style={[styles.backButton, isDark && styles.backButtonDark]}
          onPress={() => router.back()}
        >
          <Text style={[styles.backText, isDark && styles.backTextDark]}>
            ←
          </Text>
        </Pressable>

        {/* Connection indicator */}
        <View
          style={[
            styles.connectionDot,
            { backgroundColor: connected ? "#10B981" : "#6B7280" },
          ]}
        />
      </View>

      {/* Bottom panel */}
      <View style={[styles.bottomPanel, isDark && styles.bottomPanelDark]}>
        {approachingStop && (
          <UpcomingStop
            stop={approachingStop}
            distanceM={approachDist}
            visible={!!approachingStop}
          />
        )}

        <CurrentSegment segment={currentSegment} progress={progress} />

        <View style={styles.controls}>
          {!isSimulating ? (
            <Pressable
              style={styles.startButton}
              onPress={handleStartSimulation}
            >
              <Text style={styles.startButtonText}>
                {progress > 0 ? "Resume" : "Start Simulation"}
              </Text>
            </Pressable>
          ) : (
            <Pressable
              style={styles.stopButton}
              onPress={handleStopSimulation}
            >
              <Text style={styles.stopButtonText}>Pause</Text>
            </Pressable>
          )}

          <View style={styles.speedRow}>
            <Text style={[styles.speedLabel, isDark && styles.speedLabelDark]}>
              Speed:
            </Text>
            {SPEED_OPTIONS.map((s) => (
              <Pressable
                key={s}
                style={[
                  styles.speedChip,
                  s === speedMultiplier && styles.speedChipActive,
                ]}
                onPress={() => setSpeedMultiplier(s)}
              >
                <Text
                  style={[
                    styles.speedChipText,
                    s === speedMultiplier && styles.speedChipTextActive,
                  ]}
                >
                  {s}x
                </Text>
              </Pressable>
            ))}
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  center: { justifyContent: "center", alignItems: "center" },
  bgDark: { backgroundColor: "#111827" },
  loadingText: { color: "#6B7280", fontSize: 16 },
  mapContainer: { flex: 1, position: "relative" },
  toast: {
    position: "absolute", top: 60, left: 20, right: 20,
    backgroundColor: "rgba(31, 41, 55, 0.9)",
    borderRadius: 10, padding: 12, alignItems: "center",
  },
  toastText: { color: "#fff", fontSize: 14, fontWeight: "600" },
  backButton: {
    position: "absolute", top: 12, left: 16, width: 40, height: 40,
    borderRadius: 20, backgroundColor: "#fff",
    alignItems: "center", justifyContent: "center",
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15, shadowRadius: 4, elevation: 3,
  },
  backButtonDark: { backgroundColor: "#1F2937" },
  backText: { fontSize: 20, color: "#1F2937" },
  backTextDark: { color: "#F9FAFB" },
  connectionDot: {
    position: "absolute", top: 20, right: 16,
    width: 10, height: 10, borderRadius: 5,
  },
  bottomPanel: {
    backgroundColor: "#fff", borderTopLeftRadius: 20, borderTopRightRadius: 20,
    padding: 16, paddingBottom: 24,
    shadowColor: "#000", shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1, shadowRadius: 12, elevation: 8,
  },
  bottomPanelDark: { backgroundColor: "#1F2937" },
  controls: { marginTop: 12 },
  startButton: {
    backgroundColor: "#4F46E5", borderRadius: 12,
    paddingVertical: 14, alignItems: "center", marginBottom: 12,
  },
  startButtonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  stopButton: {
    backgroundColor: "#EF4444", borderRadius: 12,
    paddingVertical: 14, alignItems: "center", marginBottom: 12,
  },
  stopButtonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  speedRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
  },
  speedLabel: { fontSize: 13, color: "#6B7280", marginRight: 4 },
  speedLabelDark: { color: "#9CA3AF" },
  speedChip: {
    paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16,
    backgroundColor: "#F3F4F6", borderWidth: 1, borderColor: "#E5E7EB",
  },
  speedChipActive: { backgroundColor: "#4F46E5", borderColor: "#4F46E5" },
  speedChipText: { fontSize: 13, fontWeight: "600", color: "#374151" },
  speedChipTextActive: { color: "#fff" },
});
