import React, { useState } from "react";
import {
  StyleSheet,
  View,
  Text,
  Pressable,
  ScrollView,
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

  const toggleInterest = (interest: string) => {
    const next = selectedInterests.includes(interest)
      ? selectedInterests.filter((i) => i !== interest)
      : [...selectedInterests, interest];
    setSelectedInterests(next);
    onPreferencesChange({ interests: next, avoid_types: avoidTypes });
  };

  const toggleAvoid = (type: string) => {
    const next = avoidTypes.includes(type)
      ? avoidTypes.filter((t) => t !== type)
      : [...avoidTypes, type];
    setAvoidTypes(next);
    onPreferencesChange({ interests: selectedInterests, avoid_types: next });
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
});
