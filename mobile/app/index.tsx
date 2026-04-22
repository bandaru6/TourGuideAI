import React, { useState, useEffect, useCallback } from "react";
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  useColorScheme,
} from "react-native";
import { useRouter } from "expo-router";
import { createTrip, getDemoTrip, listTrips } from "../services/api";
import PreferencesForm from "../components/trip/PreferencesForm";
import type { UserPreferences } from "../types";

interface TripSummary {
  id: string;
  origin: string;
  destination: string;
  state: string;
  total_distance_m: number;
  total_duration_s: number;
  stops_count: number;
}

const EXAMPLE_TRIPS = [
  { origin: "San Francisco, CA", destination: "Los Angeles, CA", label: "SF → LA", desc: "Pacific Coast Highway" },
  { origin: "Las Vegas, NV", destination: "Grand Canyon, AZ", label: "Vegas → Grand Canyon", desc: "Desert adventure" },
  { origin: "Seattle, WA", destination: "Portland, OR", label: "Seattle → Portland", desc: "Pacific Northwest" },
  { origin: "Miami, FL", destination: "Key West, FL", label: "Miami → Key West", desc: "Overseas Highway" },
];

export default function TripPlanner() {
  const router = useRouter();
  const isDark = useColorScheme() === "dark";

  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [preferences, setPreferences] = useState<Partial<UserPreferences>>({});
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState("");

  // Trip history
  const [pastTrips, setPastTrips] = useState<TripSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const trips = await listTrips();
      setPastTrips(trips as unknown as TripSummary[]);
    } catch {
      // History is non-critical, silently fail
    } finally {
      setHistoryLoading(false);
    }
  };

  const handlePlanTrip = useCallback(async () => {
    if (!origin.trim() || !destination.trim()) {
      setError("Please enter both origin and destination");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const trip = await createTrip({
        origin: origin.trim(),
        destination: destination.trim(),
        preferences,
      });
      router.push(`/trip/${trip.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create trip");
    } finally {
      setLoading(false);
    }
  }, [origin, destination, preferences, router]);

  const handleDemo = useCallback(async () => {
    setDemoLoading(true);
    setError("");
    try {
      await getDemoTrip();
      router.push("/trip/demo");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo");
    } finally {
      setDemoLoading(false);
    }
  }, [router]);

  const handleExampleTrip = useCallback(
    async (ex: { origin: string; destination: string }) => {
      setLoading(true);
      setError("");
      try {
        const trip = await createTrip({
          origin: ex.origin,
          destination: ex.destination,
          preferences,
        });
        router.push(`/trip/${trip.id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create trip");
      } finally {
        setLoading(false);
      }
    },
    [preferences, router]
  );

  const stateLabel = (state: string) => {
    switch (state) {
      case "ready": return { text: "Ready", color: "#10B981" };
      case "completed": return { text: "Completed", color: "#6366F1" };
      case "active": return { text: "Active", color: "#F59E0B" };
      case "generating": return { text: "Generating...", color: "#9CA3AF" };
      default: return { text: state, color: "#6B7280" };
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        style={[styles.flex, isDark && styles.bgDark]}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.hero}>
          <Text style={[styles.title, isDark && styles.textDark]}>
            Plan Your Road Trip
          </Text>
          <Text style={[styles.subtitle, isDark && styles.subtitleDark]}>
            Intelligent stop selection powered by geospatial analysis
          </Text>
        </View>

        {/* Trip creation form */}
        <View style={[styles.card, isDark && styles.cardDark]}>
          <Text style={[styles.inputLabel, isDark && styles.labelDark]}>
            Origin
          </Text>
          <TextInput
            style={[styles.input, isDark && styles.inputDark]}
            value={origin}
            onChangeText={setOrigin}
            placeholder="San Francisco, CA"
            placeholderTextColor={isDark ? "#6B7280" : "#9CA3AF"}
            returnKeyType="next"
          />

          <Text style={[styles.inputLabel, isDark && styles.labelDark]}>
            Destination
          </Text>
          <TextInput
            style={[styles.input, isDark && styles.inputDark]}
            value={destination}
            onChangeText={setDestination}
            placeholder="Los Angeles, CA"
            placeholderTextColor={isDark ? "#6B7280" : "#9CA3AF"}
            returnKeyType="done"
            onSubmitEditing={handlePlanTrip}
          />

          <PreferencesForm
            onPreferencesChange={setPreferences}
            initialInterests={[]}
          />

          <Pressable
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handlePlanTrip}
            disabled={loading || demoLoading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Plan Trip</Text>
            )}
          </Pressable>

          <Pressable
            style={[styles.demoButton, isDark && styles.demoButtonDark]}
            onPress={handleDemo}
            disabled={loading || demoLoading}
          >
            {demoLoading ? (
              <ActivityIndicator color="#4F46E5" />
            ) : (
              <Text
                style={[styles.demoButtonText, isDark && styles.demoButtonTextDark]}
              >
                Try Demo (SF → LA)
              </Text>
            )}
          </Pressable>
        </View>

        {error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}

        {/* Example trips */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
            Popular Routes
          </Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.exampleRow}
          >
            {EXAMPLE_TRIPS.map((ex) => (
              <Pressable
                key={ex.label}
                style={[styles.exampleCard, isDark && styles.exampleCardDark]}
                onPress={() => handleExampleTrip(ex)}
                disabled={loading}
              >
                <Text style={[styles.exampleLabel, isDark && styles.textDark]}>
                  {ex.label}
                </Text>
                <Text style={[styles.exampleDesc, isDark && styles.subtitleDark]}>
                  {ex.desc}
                </Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>

        {/* About link */}
        <Pressable
          style={styles.aboutLink}
          onPress={() => router.push("/about")}
        >
          <Text style={[styles.aboutText, isDark && styles.subtitleDark]}>
            About TourGuideAI
          </Text>
        </Pressable>

        {/* Trip history */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
            Your Trips
          </Text>
          {historyLoading ? (
            <ActivityIndicator
              color="#4F46E5"
              style={{ marginTop: 12 }}
            />
          ) : pastTrips.length === 0 ? (
            <View style={[styles.emptyCard, isDark && styles.cardDark]}>
              <Text style={[styles.emptyText, isDark && styles.subtitleDark]}>
                No trips yet. Plan your first trip above or try the demo!
              </Text>
            </View>
          ) : (
            pastTrips.map((t) => {
              const st = stateLabel(t.state);
              return (
                <Pressable
                  key={t.id}
                  style={[styles.historyCard, isDark && styles.cardDark]}
                  onPress={() => router.push(`/trip/${t.id}`)}
                >
                  <View style={styles.historyHeader}>
                    <Text
                      style={[styles.historyRoute, isDark && styles.textDark]}
                      numberOfLines={1}
                    >
                      {t.origin} → {t.destination}
                    </Text>
                    <View style={[styles.stateBadge, { backgroundColor: st.color + "20" }]}>
                      <Text style={[styles.stateText, { color: st.color }]}>
                        {st.text}
                      </Text>
                    </View>
                  </View>
                  <View style={styles.historyMeta}>
                    {t.total_distance_m > 0 && (
                      <Text style={styles.historyDetail}>
                        {(t.total_distance_m / 1000).toFixed(0)} km
                      </Text>
                    )}
                    {t.total_duration_s > 0 && (
                      <Text style={styles.historyDetail}>
                        {(t.total_duration_s / 3600).toFixed(1)} hrs
                      </Text>
                    )}
                    {t.stops_count > 0 && (
                      <Text style={styles.historyDetail}>
                        {t.stops_count} stops
                      </Text>
                    )}
                  </View>
                </Pressable>
              );
            })
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  bgDark: { backgroundColor: "#111827" },
  content: { padding: 20, paddingBottom: 40 },
  hero: { marginBottom: 24, marginTop: 8 },
  title: { fontSize: 28, fontWeight: "800", color: "#1F2937", marginBottom: 4 },
  textDark: { color: "#F9FAFB" },
  subtitle: { fontSize: 15, color: "#6B7280" },
  subtitleDark: { color: "#9CA3AF" },
  card: {
    backgroundColor: "#fff", borderRadius: 16, padding: 20,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08, shadowRadius: 12, elevation: 3,
  },
  cardDark: { backgroundColor: "#1F2937" },
  inputLabel: { fontSize: 13, fontWeight: "600", color: "#374151", marginBottom: 6, marginTop: 4 },
  labelDark: { color: "#D1D5DB" },
  input: {
    backgroundColor: "#F9FAFB", borderWidth: 1, borderColor: "#E5E7EB",
    borderRadius: 10, padding: 12, fontSize: 16, color: "#1F2937", marginBottom: 16,
  },
  inputDark: { backgroundColor: "#374151", borderColor: "#4B5563", color: "#F9FAFB" },
  button: {
    backgroundColor: "#4F46E5", borderRadius: 12, paddingVertical: 14,
    alignItems: "center", marginTop: 8,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  demoButton: {
    borderWidth: 1, borderColor: "#E5E7EB", borderRadius: 12,
    paddingVertical: 14, alignItems: "center", marginTop: 12,
  },
  demoButtonDark: { borderColor: "#4B5563" },
  demoButtonText: { color: "#4F46E5", fontSize: 15, fontWeight: "600" },
  demoButtonTextDark: { color: "#818CF8" },
  errorBox: {
    backgroundColor: "#FEF2F2", borderWidth: 1, borderColor: "#FECACA",
    borderRadius: 12, padding: 16, marginTop: 16,
  },
  errorText: { color: "#991B1B", fontSize: 14 },

  // Sections
  section: { marginTop: 28 },
  sectionTitle: { fontSize: 18, fontWeight: "700", color: "#1F2937", marginBottom: 12 },

  // Example trips
  exampleRow: { gap: 12, paddingBottom: 4 },
  exampleCard: {
    backgroundColor: "#fff", borderRadius: 12, padding: 16,
    width: 180, shadowColor: "#000", shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06, shadowRadius: 6, elevation: 2,
    borderWidth: 1, borderColor: "#F3F4F6",
  },
  exampleCardDark: { backgroundColor: "#1F2937", borderColor: "#374151" },
  exampleLabel: { fontSize: 14, fontWeight: "700", color: "#1F2937", marginBottom: 4 },
  exampleDesc: { fontSize: 12, color: "#6B7280" },

  // History
  historyCard: {
    backgroundColor: "#fff", borderRadius: 12, padding: 14, marginBottom: 8,
    shadowColor: "#000", shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05, shadowRadius: 4, elevation: 1,
  },
  historyHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  historyRoute: { fontSize: 15, fontWeight: "600", color: "#1F2937", flex: 1, marginRight: 8 },
  stateBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  stateText: { fontSize: 11, fontWeight: "600", textTransform: "uppercase", letterSpacing: 0.3 },
  historyMeta: { flexDirection: "row", gap: 12 },
  historyDetail: { fontSize: 12, color: "#6B7280" },
  emptyCard: {
    backgroundColor: "#fff", borderRadius: 12, padding: 20,
    alignItems: "center",
  },
  emptyText: { fontSize: 14, color: "#6B7280", textAlign: "center" },
  aboutLink: { marginTop: 24, alignItems: "center", paddingVertical: 8 },
  aboutText: { fontSize: 14, color: "#6B7280", textDecorationLine: "underline" },
});
