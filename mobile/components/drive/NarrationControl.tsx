import React from "react";
import { StyleSheet, Pressable, Text, useColorScheme } from "react-native";

interface Props {
  enabled: boolean;
  onToggle: () => void;
}

export default function NarrationControl({ enabled, onToggle }: Props) {
  const isDark = useColorScheme() === "dark";

  return (
    <Pressable
      style={[
        styles.button,
        isDark && styles.buttonDark,
        !enabled && styles.buttonMuted,
      ]}
      onPress={onToggle}
    >
      <Text style={styles.icon}>{enabled ? "\u{1F50A}" : "\u{1F507}"}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    position: "absolute",
    top: 12,
    right: 52,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  buttonDark: {
    backgroundColor: "#1F2937",
  },
  buttonMuted: {
    opacity: 0.6,
  },
  icon: {
    fontSize: 18,
  },
});
