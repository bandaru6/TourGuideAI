import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useColorScheme } from "react-native";

export default function RootLayout() {
  const scheme = useColorScheme();
  const isDark = scheme === "dark";

  return (
    <>
      <StatusBar style={isDark ? "light" : "dark"} />
      <Stack
        screenOptions={{
          headerStyle: {
            backgroundColor: isDark ? "#111827" : "#fff",
          },
          headerTintColor: isDark ? "#F9FAFB" : "#1F2937",
          headerTitleStyle: {
            fontWeight: "700",
          },
          contentStyle: {
            backgroundColor: isDark ? "#111827" : "#F9FAFB",
          },
        }}
      >
        <Stack.Screen
          name="index"
          options={{ title: "TourGuideAI" }}
        />
        <Stack.Screen
          name="trip/[id]"
          options={{ title: "Trip Review" }}
        />
        <Stack.Screen
          name="drive/[id]"
          options={{
            title: "Drive Mode",
            headerShown: false,
          }}
        />
        <Stack.Screen
          name="about"
          options={{ title: "About" }}
        />
      </Stack>
    </>
  );
}
