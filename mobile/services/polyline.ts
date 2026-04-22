/**
 * Decode a Google-encoded polyline string into an array of {latitude, longitude}.
 * Compatible with react-native-maps coordinate format.
 */
export function decodePolyline(
  encoded: string
): { latitude: number; longitude: number }[] {
  const points: { latitude: number; longitude: number }[] = [];
  let index = 0;
  let lat = 0;
  let lng = 0;

  while (index < encoded.length) {
    let shift = 0;
    let result = 0;
    let byte: number;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    lat += result & 1 ? ~(result >> 1) : result >> 1;

    shift = 0;
    result = 0;

    do {
      byte = encoded.charCodeAt(index++) - 63;
      result |= (byte & 0x1f) << shift;
      shift += 5;
    } while (byte >= 0x20);

    lng += result & 1 ? ~(result >> 1) : result >> 1;

    points.push({
      latitude: lat / 1e5,
      longitude: lng / 1e5,
    });
  }

  return points;
}

/**
 * Interpolate a position along decoded polyline points at a given fraction (0-1).
 */
export function interpolateAlongPolyline(
  points: { latitude: number; longitude: number }[],
  fraction: number
): { latitude: number; longitude: number } {
  if (points.length === 0) return { latitude: 0, longitude: 0 };
  if (fraction <= 0) return points[0];
  if (fraction >= 1) return points[points.length - 1];

  // Calculate total distance
  let totalDist = 0;
  const segDists: number[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    const d = haversine(
      points[i].latitude,
      points[i].longitude,
      points[i + 1].latitude,
      points[i + 1].longitude
    );
    segDists.push(d);
    totalDist += d;
  }

  const targetDist = fraction * totalDist;
  let cumDist = 0;

  for (let i = 0; i < segDists.length; i++) {
    if (cumDist + segDists[i] >= targetDist) {
      const segFraction =
        segDists[i] > 0 ? (targetDist - cumDist) / segDists[i] : 0;
      return {
        latitude:
          points[i].latitude +
          segFraction * (points[i + 1].latitude - points[i].latitude),
        longitude:
          points[i].longitude +
          segFraction * (points[i + 1].longitude - points[i].longitude),
      };
    }
    cumDist += segDists[i];
  }

  return points[points.length - 1];
}

function haversine(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const R = 6371000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}
