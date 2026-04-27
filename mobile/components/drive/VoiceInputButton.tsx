import React, { useEffect, useRef } from "react";
import {
  StyleSheet,
  Pressable,
  Text,
  Animated,
  useColorScheme,
} from "react-native";

interface Props {
  listening: boolean;
  onPress: () => void;
  supported: boolean;
}

export default function VoiceInputButton({
  listening,
  onPress,
  supported,
}: Props) {
  const isDark = useColorScheme() === "dark";
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (listening) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.3,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.stopAnimation();
      pulseAnim.setValue(1);
    }
  }, [listening, pulseAnim]);

  if (!supported) return null;

  return (
    <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
      <Pressable
        style={[
          styles.button,
          isDark && styles.buttonDark,
          listening && styles.buttonActive,
        ]}
        onPress={onPress}
      >
        <Text style={styles.icon}>{listening ? "\u{1F534}" : "\u{1F3A4}"}</Text>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 48,
    height: 48,
    borderRadius: 24,
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
  buttonActive: {
    backgroundColor: "#FEE2E2",
  },
  icon: {
    fontSize: 22,
  },
});
