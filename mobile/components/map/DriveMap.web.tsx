import React, { forwardRef } from "react";
import WebDriveMap from "./WebDriveMap";
import type { DriveMapRef } from "./WebDriveMap";
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

const DriveMap = forwardRef<DriveMapRef, Props>(function DriveMap(props, ref) {
  return <WebDriveMap ref={ref} {...props} />;
});

export default DriveMap;
