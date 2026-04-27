import React, { useState } from "react";
import {
  StyleSheet,
  View,
  Text,
  Pressable,
  ScrollView,
  TextInput,
  useColorScheme,
} from "react-native";
import type { UserPreferences } from "../../types";

interface Props {
  onPreferencesChange: (prefs: Partial<UserPreferences>) => void;
  initialInterests?: string[];
}

const INTEREST_OPTIONS = [
  "scenic",
  "beach",
  "nature",
  "food",
  "history",
  "culture",
  "art",
  "adventure",
  "photography",
  "architecture",
];

const AVOID_OPTIONS = [
  "gas_station",
  "rest_area",
  "fast_food",
  "highway",
];

export default function PreferencesForm({
  onPreferencesChange,
  initialInterests = [],
}: Props) {
  const isDark = useColorScheme() === "dark";
  const [selectedInterests, setSelectedInterests] =
    useState<string[]>(initialInterests);
  const [avoidTypes, setAvoidTypes] = useState<string[]>([]);
  const [evMode, setEvMode] = useState(false);
  const [vehicleRange, setVehicleRange] = useState("");

  const emitChange = (
    interests: string[],
    avoid: string[],
    ev: boolean,
    range: string
  ) => {
    const prefs: Partial<UserPreferences> = {
      interests,
      avoid_types: avoid,
    };
    if (ev && range) {
      prefs.vehicle_range_km = parseFloat(range) || null;
    }
    onPreferencesChange(prefs);
  };

  const toggleInterest = (interest: string) => {
    const next = selectedInterests.includes(interest)
      ? selectedInterests.filter((i) => i !== interest)
      : [...selectedInterests, interest];
    setSelectedInterests(next);
    emitChange(next, avoidTypes, evMode, vehicleRange);
  };

  const toggleAvoid = (type: string) => {
    const next = avoidTypes.includes(type)
      ? avoidTypes.filter((t) => t !== type)
      : [...avoidTypes, type];
    setAvoidTypes(next);
    emitChange(selectedInterests, next, evMode, vehicleRange);
  };

  const toggleEvMode = () => {
    const next = !evMode;
    setEvMode(next);
    emitChange(selectedInterests, avoidTypes, next, vehicleRange);
  };

  return (
    <View style={styles.container}>
      <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
        Interests
      </Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chipRow}
      >
        {INTEREST_OPTIONS.map((interest) => {
          const selected = selectedInterests.includes(interest);
          return (
            <Pressable
              key={interest}
              style={[
                styles.chip,
                selected && styles.chipSelected,
                isDark && !selected && styles.chipDark,
              ]}
              onPress={() => toggleInterest(interest)}
            >
              <Text
                style={[
                  styles.chipText,
                  selected && styles.chipTextSelected,
                  isDark && !selected && styles.chipTextDark,
                ]}
              >
                {interest}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
        Avoid
      </Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chipRow}
      >
        {AVOID_OPTIONS.map((type) => {
          const selected = avoidTypes.includes(type);
          return (
            <Pressable
              key={type}
              style={[
                styles.chip,
                selected && styles.chipAvoidSelected,
                isDark && !selected && styles.chipDark,
              ]}
              onPress={() => toggleAvoid(type)}
            >
              <Text
                style={[
                  styles.chipText,
                  selected && styles.chipAvoidTextSelected,
                  isDark && !selected && styles.chipTextDark,
                ]}
              >
                {type.replace("_", " ")}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <Text style={[styles.sectionTitle, isDark && styles.textDark]}>
        EV Mode
      </Text>
      <View style={styles.evRow}>
        <Pressable
          style={[
            styles.chip,
            evMode && styles.chipSelected,
            isDark && !evMode && styles.chipDark,
          ]}
          onPress={toggleEvMode}
        >
          <Text
            style={[
              styles.chipText,
              evMode && styles.chipTextSelected,
              isDark && !evMode && styles.chipTextDark,
            ]}
          >
            EV Vehicle
          </Text>
        </Pressable>
        {evMode && (
          <TextInput
            style={[styles.rangeInput, isDark && styles.rangeInputDark]}
            placeholder="Range (km)"
            placeholderTextColor="#9CA3AF"
            keyboardType="numeric"
            value={vehicleRange}
            onChangeText={(text) => {
              setVehicleRange(text);
              emitChange(selectedInterests, avoidTypes, true, text);
            }}
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
    marginBottom: 8,
    marginTop: 4,
  },
  textDark: {
    color: "#D1D5DB",
  },
  chipRow: {
    flexDirection: "row",
    gap: 8,
    paddingBottom: 4,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  chipDark: {
    backgroundColor: "#374151",
    borderColor: "#4B5563",
  },
  chipSelected: {
    backgroundColor: "#4F46E5",
    borderColor: "#4F46E5",
  },
  chipAvoidSelected: {
    backgroundColor: "#EF4444",
    borderColor: "#EF4444",
  },
  chipText: {
    fontSize: 13,
    color: "#374151",
    textTransform: "capitalize",
  },
  chipTextDark: {
    color: "#D1D5DB",
  },
  chipTextSelected: {
    color: "#fff",
    fontWeight: "600",
  },
  chipAvoidTextSelected: {
    color: "#fff",
    fontWeight: "600",
  },
  evRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingBottom: 4,
  },
  rangeInput: {
    flex: 1,
    height: 36,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 13,
    color: "#374151",
    backgroundColor: "#F9FAFB",
  },
  rangeInputDark: {
    borderColor: "#4B5563",
    color: "#D1D5DB",
    backgroundColor: "#374151",
  },
});
