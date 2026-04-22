import React, { useRef, useEffect, useMemo } from "react";
import { StyleSheet, View } from "react-native";
import type { Trip } from "../../types";
import { decodePolyline } from "../../services/polyline";

interface Props {
  trip: Trip;
  carPosition?: { latitude: number; longitude: number } | null;
  style?: object;
}

/**
 * Web-only map component using Leaflet via an iframe.
 * Renders route polyline, stop markers, and optional car position.
 */
export default function WebMap({ trip, carPosition, style }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const routeCoords = useMemo(
    () => (trip.route_polyline ? decodePolyline(trip.route_polyline) : []),
    [trip.route_polyline]
  );

  const htmlContent = useMemo(() => {
    const center =
      routeCoords.length > 0
        ? routeCoords[Math.floor(routeCoords.length / 2)]
        : { latitude: 37.7749, longitude: -122.4194 };

    const polylineJs = routeCoords
      .map((c) => `[${c.latitude}, ${c.longitude}]`)
      .join(",");

    const markersJs = trip.stops
      .map((stop) => {
        const color = getMarkerColor(stop.type);
        const escapedName = stop.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
        const scoreText = stop.score
          ? `Score: ${stop.score.total_score.toFixed(2)}<br/>${stop.score.selection_reason.replace(/'/g, "\\'")}`
          : "";
        return `L.circleMarker([${stop.lat}, ${stop.lng}], {
          radius: 8, fillColor: '${color}', color: '#fff', weight: 2, fillOpacity: 0.9
        }).addTo(map).bindPopup('<b>${escapedName}</b><br/>${stop.type} · ${stop.suggested_duration_min} min<br/>${scoreText}');`;
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
var map = L.map('map').setView([${center.latitude}, ${center.longitude}], 7);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap'
}).addTo(map);

var coords = [${polylineJs}];
if (coords.length > 0) {
  var polyline = L.polyline(coords, {color: '#4F46E5', weight: 4}).addTo(map);
  map.fitBounds(polyline.getBounds(), {padding: [40, 40]});
}

${markersJs}

var carMarker = null;
window.updateCar = function(lat, lng) {
  if (carMarker) { carMarker.setLatLng([lat, lng]); }
  else {
    carMarker = L.circleMarker([lat, lng], {
      radius: 7, fillColor: '#4F46E5', color: '#fff', weight: 3, fillOpacity: 1
    }).addTo(map);
  }
  map.panTo([lat, lng]);
};
</script>
</body></html>`;
  }, [routeCoords, trip.stops]);

  // Update car position
  useEffect(() => {
    if (carPosition && iframeRef.current?.contentWindow) {
      try {
        (iframeRef.current.contentWindow as any).updateCar(
          carPosition.latitude,
          carPosition.longitude
        );
      } catch {
        // cross-origin safety
      }
    }
  }, [carPosition]);

  return (
    <View style={[styles.container, style]}>
      <iframe
        ref={iframeRef as any}
        srcDoc={htmlContent}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
          borderRadius: 12,
        }}
      />
    </View>
  );
}

function getMarkerColor(type: string): string {
  const colors: Record<string, string> = {
    scenic: "#10B981",
    viewpoint: "#10B981",
    beach: "#06B6D4",
    park: "#10B981",
    restaurant: "#F59E0B",
    cafe: "#F59E0B",
    food: "#F59E0B",
    attraction: "#6366F1",
    museum: "#8B5CF6",
    gas_station: "#6B7280",
    rest_area: "#6B7280",
  };
  return colors[type.toLowerCase()] || "#6366F1";
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    overflow: "hidden",
    borderRadius: 12,
  },
});
