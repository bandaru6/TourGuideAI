import React, { forwardRef } from "react";
import { View, StyleSheet } from "react-native";
import MapView, { Marker, Polyline, PROVIDER_DEFAULT } from "react-native-maps";
import StopMarker from "./StopMarker";
import { decodePolyline } from "../../services/polyline";
import type { Trip } from "../../types";

interface Props {
  trip: Trip;
  carPosition?: { latitude: number; longitude: number } | null;
  initialRegion?: {
    latitude: number;
    longitude: number;
    latitudeDelta: number;
    longitudeDelta: number;
  };
}

const DriveMap = forwardRef<MapView, Props>(function DriveMap(
  { trip, carPosition, initialRegion },
  ref
) {
  const routeCoords = React.useMemo(
    () => (trip.route_polyline ? decodePolyline(trip.route_polyline) : []),
    [trip.route_polyline]
  );

  return (
    <MapView
      ref={ref}
      style={styles.map}
      provider={PROVIDER_DEFAULT}
      initialRegion={initialRegion}
    >
      {routeCoords.length > 0 && (
        <Polyline
          coordinates={routeCoords}
          strokeColor="#4F46E5"
          strokeWidth={4}
        />
      )}
      {trip.stops.map((stop) => (
        <StopMarker key={stop.id} stop={stop} />
      ))}
      {carPosition && (
        <Marker coordinate={carPosition} anchor={{ x: 0.5, y: 0.5 }} flat>
          <View style={styles.carMarker}>
            <View style={styles.carPulse} />
            <View style={styles.carDot} />
          </View>
        </Marker>
      )}
    </MapView>
  );
});

export default DriveMap;

const styles = StyleSheet.create({
  map: { flex: 1 },
  carMarker: {
    width: 28, height: 28,
    alignItems: "center", justifyContent: "center",
  },
  carPulse: {
    position: "absolute", width: 28, height: 28, borderRadius: 14,
    backgroundColor: "rgba(79, 70, 229, 0.15)",
  },
  carDot: {
    width: 14, height: 14, borderRadius: 7,
    backgroundColor: "#4F46E5", borderWidth: 2.5, borderColor: "#fff",
    shadowColor: "#4F46E5", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5, shadowRadius: 6, elevation: 4,
  },
});
