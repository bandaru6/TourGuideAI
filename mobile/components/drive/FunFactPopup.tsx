import React, { useEffect, useRef } from "react";
import {
  StyleSheet,
  View,
  Text,
  Pressable,
  Animated,
  useColorScheme,
} from "react-native";

interface Props {
  text: string;
  visible: boolean;
  onDismiss: () => void;
}

export default function FunFactPopup({ text, visible, onDismiss }: Props) {
  const isDark = useColorScheme() === "dark";
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(opacity, {
          toValue: 1,
          useNativeDriver: true,
        }),
        Animated.spring(scale, {
          toValue: 1,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }),
      ]).start();

      // Auto-dismiss after 8 seconds
      const timer = setTimeout(onDismiss, 8000);
      return () => clearTimeout(timer);
    } else {
      Animated.parallel([
        Animated.timing(opacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(scale, {
          toValue: 0.9,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, opacity, scale, onDismiss]);

  if (!visible && !text) return null;

  return (
    <Animated.View
      style={[
        styles.overlay,
        { opacity, transform: [{ scale }] },
      ]}
      pointerEvents={visible ? "auto" : "none"}
    >
      <Pressable
        style={[styles.card, isDark && styles.cardDark]}
        onPress={onDismiss}
      >
        <Text style={styles.emoji}>💡</Text>
        <Text style={[styles.title, isDark && styles.titleDark]}>
          Did you know?
        </Text>
        <Text style={[styles.text, isDark && styles.textDark]}>{text}</Text>
        <Text style={styles.dismiss}>Tap to dismiss</Text>
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    position: "absolute",
    top: 100,
    left: 20,
    right: 20,
    zIndex: 100,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 16,
    elevation: 8,
    alignItems: "center",
  },
  cardDark: {
    backgroundColor: "#1F2937",
  },
  emoji: {
    fontSize: 28,
    marginBottom: 8,
  },
  title: {
    fontSize: 14,
    fontWeight: "700",
    color: "#4F46E5",
    marginBottom: 8,
  },
  titleDark: {
    color: "#818CF8",
  },
  text: {
    fontSize: 15,
    color: "#374151",
    lineHeight: 22,
    textAlign: "center",
  },
  textDark: {
    color: "#D1D5DB",
  },
  dismiss: {
    fontSize: 11,
    color: "#9CA3AF",
    marginTop: 12,
  },
});
