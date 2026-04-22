import React from "react";
import {
  StyleSheet,
  View,
  Text,
  ScrollView,
  useColorScheme,
  Linking,
  Pressable,
} from "react-native";

const VERSION = "1.0.0";

const TECH_STACK = [
  { label: "Frontend", value: "React Native (Expo)" },
  { label: "Navigation", value: "Expo Router" },
  { label: "Maps", value: "react-native-maps / Leaflet" },
  { label: "Backend", value: "FastAPI (Python)" },
  { label: "Routing", value: "OSRM (Open Source)" },
  { label: "Places", value: "OpenStreetMap / Overpass" },
  { label: "Geocoding", value: "Nominatim" },
  { label: "Enrichment", value: "Google Gemini (optional)" },
  { label: "Database", value: "SQLite" },
];

const FEATURES = [
  "Deterministic geospatial corridor engine",
  "Multi-factor stop ranking (5 scoring dimensions)",
  "Explainable stop selection with score breakdowns",
  "Real-time drive simulation with event engine",
  "State machine for trip lifecycle management",
  "WebSocket-based live drive events",
  "Polyline interpolation for GPS simulation",
  "Retry with exponential backoff for external APIs",
  "Geocoding cache for repeated lookups",
  "Dark mode support",
];

export default function About() {
  const isDark = useColorScheme() === "dark";

  return (
    <ScrollView
      style={[styles.container, isDark && styles.bgDark]}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={[styles.appName, isDark && styles.textDark]}>
          TourGuideAI
        </Text>
        <Text style={[styles.version, isDark && styles.textMuted]}>
          v{VERSION}
        </Text>
        <Text style={[styles.tagline, isDark && styles.textMuted]}>
          Intelligent road trip planning with geospatial precision
        </Text>
      </View>

      <View style={[styles.card, isDark && styles.cardDark]}>
        <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
          About
        </Text>
        <Text style={[styles.body, isDark && styles.textMuted]}>
          TourGuideAI is a full-stack road trip planning copilot that
          discovers interesting stops along your route using a deterministic
          geospatial corridor engine. Unlike simple radius searches, it
          builds a corridor along your actual driving path, scores candidates
          across multiple dimensions, and assembles an optimized itinerary.
        </Text>
      </View>

      <View style={[styles.card, isDark && styles.cardDark]}>
        <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
          Key Features
        </Text>
        {FEATURES.map((f, i) => (
          <View key={i} style={styles.featureRow}>
            <Text style={styles.bullet}>·</Text>
            <Text style={[styles.featureText, isDark && styles.textMuted]}>
              {f}
            </Text>
          </View>
        ))}
      </View>

      <View style={[styles.card, isDark && styles.cardDark]}>
        <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
          Tech Stack
        </Text>
        {TECH_STACK.map((item, i) => (
          <View key={i} style={styles.techRow}>
            <Text style={[styles.techLabel, isDark && styles.textMuted]}>
              {item.label}
            </Text>
            <Text style={[styles.techValue, isDark && styles.textDark]}>
              {item.value}
            </Text>
          </View>
        ))}
      </View>

      <View style={[styles.card, isDark && styles.cardDark]}>
        <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
          Architecture
        </Text>
        <Text style={[styles.body, isDark && styles.textMuted]}>
          The backend uses a pipeline architecture: Route → Corridor →
          Candidates → Ranking → Itinerary → Segments → Enrichment. Each
          step is deterministic and explainable — no black-box LLM decisions
          for core geospatial logic. Gemini is used only for optional
          enrichment (descriptions, fun facts).
        </Text>
      </View>

      <Pressable
        style={styles.linkButton}
        onPress={() =>
          Linking.openURL("https://github.com/aashrithbandaru/TourGuideAI")
        }
      >
        <Text style={styles.linkText}>View on GitHub</Text>
      </Pressable>

      <Text style={[styles.footer, isDark && styles.textMuted]}>
        Built by Aashrith Bandaru
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bgDark: { backgroundColor: "#111827" },
  content: { padding: 16, paddingBottom: 60 },
  header: { alignItems: "center", marginBottom: 24, marginTop: 8 },
  appName: {
    fontSize: 28,
    fontWeight: "800",
    color: "#4F46E5",
  },
  version: {
    fontSize: 14,
    color: "#6B7280",
    marginTop: 4,
  },
  tagline: {
    fontSize: 14,
    color: "#6B7280",
    marginTop: 8,
    textAlign: "center",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  cardDark: { backgroundColor: "#1F2937" },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 10,
  },
  body: {
    fontSize: 14,
    color: "#4B5563",
    lineHeight: 21,
  },
  featureRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 6,
  },
  bullet: {
    color: "#4F46E5",
    fontSize: 18,
    fontWeight: "700",
    marginRight: 8,
    lineHeight: 20,
  },
  featureText: {
    flex: 1,
    fontSize: 14,
    color: "#4B5563",
    lineHeight: 20,
  },
  techRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 6,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#E5E7EB",
  },
  techLabel: {
    fontSize: 14,
    color: "#6B7280",
  },
  techValue: {
    fontSize: 14,
    color: "#1F2937",
    fontWeight: "600",
  },
  linkButton: {
    backgroundColor: "#4F46E5",
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
    marginBottom: 16,
  },
  linkText: {
    color: "#fff",
    fontSize: 15,
    fontWeight: "600",
  },
  footer: {
    textAlign: "center",
    fontSize: 13,
    color: "#9CA3AF",
    marginBottom: 20,
  },
  textDark: { color: "#F9FAFB" },
  textMuted: { color: "#9CA3AF" },
});
