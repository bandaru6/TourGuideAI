import React, { useCallback } from "react";
import {
  StyleSheet,
  View,
  Text,
  FlatList,
  Pressable,
  ActivityIndicator,
  useColorScheme,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTrip } from "../../hooks/useTrip";
import { startTrip } from "../../services/api";
import MapWrapper from "../../components/map/MapWrapper";
import StopCard from "../../components/trip/StopCard";
import SegmentTimeline from "../../components/trip/SegmentTimeline";

export default function TripReview() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const isDark = useColorScheme() === "dark";
  const { trip, loading, error, refresh } = useTrip(id);

  const handleStartDrive = useCallback(async () => {
    if (!trip) return;
    try {
      if (trip.state === "ready") {
        await startTrip(trip.id);
      }
      router.push(`/drive/${trip.id}`);
    } catch (err) {
      console.error("Failed to start drive:", err);
      // Navigate anyway for demo trips
      router.push(`/drive/${trip.id}`);
    }
  }, [trip, router]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={[styles.loadingText, isDark && styles.textMuted]}>
          Loading trip...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorIcon}>!</Text>
        <Text style={[styles.errorTitle, isDark && styles.textDark]}>
          Something went wrong
        </Text>
        <Text style={styles.errorText}>{error}</Text>
        <Pressable style={styles.retryButton} onPress={refresh}>
          <Text style={styles.retryText}>Try Again</Text>
        </Pressable>
        <Pressable
          style={styles.backLink}
          onPress={() => router.back()}
        >
          <Text style={styles.backLinkText}>Go Back</Text>
        </Pressable>
      </View>
    );
  }

  if (!trip) return null;

  if (trip.state === "generating") {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={[styles.generatingTitle, isDark && styles.textDark]}>
          Generating your trip...
        </Text>
        <Text style={[styles.generatingSubtitle, isDark && styles.textMuted]}>
          Finding the best stops along your route
        </Text>
      </View>
    );
  }

  const distKm = (trip.total_distance_m / 1000).toFixed(0);
  const durationHr = (trip.total_duration_s / 3600).toFixed(1);

  const renderItem = ({ item, index }: { item: typeof trip.stops[0]; index: number }) => (
    <View>
      {trip.segments[index] && (
        <SegmentTimeline segment={trip.segments[index]} />
      )}
      <StopCard stop={item} index={index} />
    </View>
  );

  return (
    <FlatList
      style={[styles.flex, isDark && styles.bgDark]}
      contentContainerStyle={styles.content}
      ListHeaderComponent={
        <>
          <View style={styles.summaryCard}>
            <Text style={[styles.routeTitle, isDark && styles.textDark]}>
              {trip.origin} → {trip.destination}
            </Text>
            <View style={styles.statsRow}>
              <View style={styles.stat}>
                <Text style={styles.statValue}>{distKm}</Text>
                <Text style={styles.statLabel}>km</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.stat}>
                <Text style={styles.statValue}>{durationHr}</Text>
                <Text style={styles.statLabel}>hours</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.stat}>
                <Text style={styles.statValue}>{trip.stops.length}</Text>
                <Text style={styles.statLabel}>stops</Text>
              </View>
            </View>
          </View>

          {trip.route_polyline ? (
            <View style={styles.mapContainer}>
              <MapWrapper trip={trip} />
            </View>
          ) : null}

          <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
            Stops
          </Text>
        </>
      }
      data={trip.stops}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      ListEmptyComponent={
        <View style={styles.emptyStops}>
          <Text style={[styles.emptyStopsText, isDark && styles.textMuted]}>
            No stops found along this route. Try adjusting your interests or choosing a longer route.
          </Text>
        </View>
      }
      ListFooterComponent={
        <View style={styles.footer}>
          {trip.segments[trip.stops.length] && (
            <SegmentTimeline segment={trip.segments[trip.stops.length]} />
          )}
          <Pressable style={styles.driveButton} onPress={handleStartDrive}>
            <Text style={styles.driveButtonText}>Start Drive</Text>
          </Pressable>
        </View>
      }
    />
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  bgDark: { backgroundColor: "#111827" },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
    color: "#6B7280",
  },
  errorIcon: {
    fontSize: 32,
    fontWeight: "800",
    color: "#fff",
    backgroundColor: "#EF4444",
    width: 48,
    height: 48,
    borderRadius: 24,
    textAlign: "center",
    lineHeight: 48,
    marginBottom: 12,
    overflow: "hidden",
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 8,
  },
  errorText: {
    color: "#6B7280",
    fontSize: 14,
    textAlign: "center",
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    borderRadius: 10,
    paddingHorizontal: 24,
    paddingVertical: 10,
    marginBottom: 12,
  },
  retryText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
  },
  backLink: {
    paddingVertical: 8,
  },
  backLinkText: {
    color: "#4F46E5",
    fontSize: 14,
  },
  textDark: { color: "#F9FAFB" },
  textMuted: { color: "#9CA3AF" },
  generatingTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1F2937",
    marginTop: 16,
  },
  generatingSubtitle: {
    fontSize: 15,
    color: "#6B7280",
    marginTop: 4,
  },
  summaryCard: {
    marginBottom: 16,
  },
  routeTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: "#1F2937",
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#EEF2FF",
    borderRadius: 12,
    padding: 12,
  },
  stat: {
    flex: 1,
    alignItems: "center",
  },
  statValue: {
    fontSize: 20,
    fontWeight: "800",
    color: "#4F46E5",
  },
  statLabel: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 28,
    backgroundColor: "#C7D2FE",
  },
  mapContainer: {
    height: 280,
    borderRadius: 12,
    overflow: "hidden",
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 12,
  },
  footer: {
    marginTop: 8,
  },
  driveButton: {
    backgroundColor: "#4F46E5",
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 16,
  },
  driveButtonText: {
    color: "#fff",
    fontSize: 17,
    fontWeight: "700",
  },
  emptyStops: {
    padding: 24,
    alignItems: "center",
  },
  emptyStopsText: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 20,
  },
});
