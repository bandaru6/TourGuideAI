import React from "react";
import type { Trip } from "../../types";
import WebMap from "./WebMap";

interface Props {
  trip: Trip;
  carPosition?: { latitude: number; longitude: number } | null;
  style?: object;
}

export default function MapWrapper(props: Props) {
  return <WebMap {...props} />;
}
