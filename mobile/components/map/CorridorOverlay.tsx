import React from "react";
import { Polygon } from "react-native-maps";
import type { CorridorGeometry } from "../../types";

interface Props {
  corridor: CorridorGeometry;
}

/**
 * Renders a semi-transparent polygon showing the search corridor
 * by offsetting sample points left and right by corridor_width_m.
 */
export default function CorridorOverlay({ corridor }: Props) {
  const coords = React.useMemo(() => {
    const { sample_points, corridor_width_m } = corridor;
    if (sample_points.length < 2) return [];

    const offsetM = corridor_width_m;
    // Approximate degrees per meter at average latitude
    const avgLat =
      sample_points.reduce((s, p) => s + p.lat, 0) / sample_points.length;
    const mPerDegLat = 111320;
    const mPerDegLng = 111320 * Math.cos((avgLat * Math.PI) / 180);

    const left: { latitude: number; longitude: number }[] = [];
    const right: { latitude: number; longitude: number }[] = [];

    for (const pt of sample_points) {
      const bearingRad = ((pt.bearing - 90) * Math.PI) / 180;
      const dLat = (offsetM * Math.cos(bearingRad)) / mPerDegLat;
      const dLng = (offsetM * Math.sin(bearingRad)) / mPerDegLng;

      left.push({
        latitude: pt.lat + dLat,
        longitude: pt.lng + dLng,
      });

      const bearingRad2 = ((pt.bearing + 90) * Math.PI) / 180;
      const dLat2 = (offsetM * Math.cos(bearingRad2)) / mPerDegLat;
      const dLng2 = (offsetM * Math.sin(bearingRad2)) / mPerDegLng;

      right.push({
        latitude: pt.lat + dLat2,
        longitude: pt.lng + dLng2,
      });
    }

    // Form a closed polygon: left forward, right reversed
    return [...left, ...right.reverse()];
  }, [corridor]);

  if (coords.length < 3) return null;

  return (
    <Polygon
      coordinates={coords}
      fillColor="rgba(79, 70, 229, 0.08)"
      strokeColor="rgba(79, 70, 229, 0.2)"
      strokeWidth={1}
    />
  );
}
