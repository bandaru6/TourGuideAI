import React, { useRef, useEffect, useMemo, useImperativeHandle, forwardRef } from "react";
import { StyleSheet, View } from "react-native";
import type { Trip } from "../../types";
import { decodePolyline } from "../../services/polyline";

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

export interface DriveMapRef {
  animateCamera: (config: { center: { latitude: number; longitude: number }; zoom: number }, opts: { duration: number }) => void;
}

const WebDriveMap = forwardRef<DriveMapRef, Props>(function WebDriveMap(
  { trip, carPosition, initialRegion },
  ref
) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const routeCoords = useMemo(
    () => (trip.route_polyline ? decodePolyline(trip.route_polyline) : []),
    [trip.route_polyline]
  );

  useImperativeHandle(ref, () => ({
    animateCamera(config, _opts) {
      if (iframeRef.current?.contentWindow) {
        try {
          (iframeRef.current.contentWindow as any).panTo(
            config.center.latitude,
            config.center.longitude,
            config.zoom
          );
        } catch {}
      }
    },
  }));

  const htmlContent = useMemo(() => {
    const center = initialRegion || (
      routeCoords.length > 0
        ? routeCoords[Math.floor(routeCoords.length / 2)]
        : { latitude: 37.7749, longitude: -122.4194 }
    );

    const polylineJs = routeCoords
      .map((c) => `[${c.latitude}, ${c.longitude}]`)
      .join(",");

    const markersJs = trip.stops
      .map((stop) => {
        const color = getMarkerColor(stop.type);
        const escapedName = stop.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
        return `L.circleMarker([${stop.lat}, ${stop.lng}], {
          radius: 8, fillColor: '${color}', color: '#fff', weight: 2, fillOpacity: 0.9
        }).addTo(map).bindPopup('<b>${escapedName}</b><br/>${stop.type}');`;
      })
      .join("\n");

    return `<!DOCTYPE html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{margin:0;padding:0;width:100%;height:100%;}</style>
</head><body>
<div id="map"></div>
<script>
var map = L.map('map').setView([${center.latitude}, ${center.longitude}], 8);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OSM'
}).addTo(map);

var coords = [${polylineJs}];
if (coords.length > 0) {
  L.polyline(coords, {color: '#4F46E5', weight: 4}).addTo(map);
  map.fitBounds(L.latLngBounds(coords), {padding: [30, 30]});
}

${markersJs}

var carMarker = null;
window.updateCar = function(lat, lng) {
  if (carMarker) { carMarker.setLatLng([lat, lng]); }
  else {
    carMarker = L.circleMarker([lat, lng], {
      radius: 8, fillColor: '#4F46E5', color: '#fff', weight: 3, fillOpacity: 1
    }).addTo(map);
  }
};
window.panTo = function(lat, lng, zoom) {
  map.setView([lat, lng], zoom || map.getZoom(), {animate: true, duration: 0.3});
};
</script>
</body></html>`;
  }, [routeCoords, trip.stops, initialRegion]);

  useEffect(() => {
    if (carPosition && iframeRef.current?.contentWindow) {
      try {
        (iframeRef.current.contentWindow as any).updateCar(
          carPosition.latitude,
          carPosition.longitude
        );
      } catch {}
    }
  }, [carPosition]);

  return (
    <View style={styles.container}>
      <iframe
        ref={iframeRef as any}
        srcDoc={htmlContent}
        style={{ width: "100%", height: "100%", border: "none" }}
      />
    </View>
  );
});

export default WebDriveMap;

function getMarkerColor(type: string): string {
  const colors: Record<string, string> = {
    scenic: "#10B981", viewpoint: "#10B981", beach: "#06B6D4",
    park: "#10B981", restaurant: "#F59E0B", cafe: "#F59E0B",
    attraction: "#6366F1", museum: "#8B5CF6",
  };
  return colors[type.toLowerCase()] || "#6366F1";
}

const styles = StyleSheet.create({
  container: { flex: 1 },
});
