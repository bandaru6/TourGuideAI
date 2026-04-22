import React, { useRef, useEffect } from "react";
import { StyleSheet, View } from "react-native";
import MapView, { Marker, Polyline, PROVIDER_DEFAULT } from "react-native-maps";
import type { Trip } from "../../types";
import { decodePolyline } from "../../services/polyline";
import StopMarker from "./StopMarker";
import CorridorOverlay from "./CorridorOverlay";

interface Props {
  trip: Trip;
  carPosition?: { latitude: number; longitude: number } | null;
  style?: object;
}

export default function RouteMap({ trip, carPosition, style }: Props) {
  const mapRef = useRef<MapView>(null);

  const routeCoords = React.useMemo(
    () => (trip.route_polyline ? decodePolyline(trip.route_polyline) : []),
    [trip.route_polyline]
  );

  useEffect(() => {
    if (mapRef.current && routeCoords.length > 0) {
      setTimeout(() => {
        mapRef.current?.fitToCoordinates(routeCoords, {
          edgePadding: { top: 60, right: 40, bottom: 60, left: 40 },
          animated: true,
        });
      }, 500);
    }
  }, [routeCoords]);

  return (
    <View style={[styles.container, style]}>
      <MapView
        ref={mapRef}
        style={styles.map}
        provider={PROVIDER_DEFAULT}
        showsUserLocation={false}
        showsCompass
        showsScale
      >
        {trip.corridor && (
          <CorridorOverlay corridor={trip.corridor} />
        )}

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
          <Marker
            coordinate={carPosition}
            title="You"
            anchor={{ x: 0.5, y: 0.5 }}
          >
            <View style={styles.carMarker}>
              <View style={styles.carDot} />
            </View>
          </Marker>
        )}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: "hidden",
    borderRadius: 12,
  },
  map: {
    flex: 1,
  },
  carMarker: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "rgba(79, 70, 229, 0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
  carDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: "#4F46E5",
    borderWidth: 2,
    borderColor: "#fff",
  },
});
