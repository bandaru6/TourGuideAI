import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.db.store import TripStore
from app.dependencies import get_store
from app.engine.drive_events import DriveEventEngine
from app.engine.geo_utils import decode_polyline
from app.models.drive_events import TripState
from app.services.polyline_interpolator import PolylineInterpolator

router = APIRouter(tags=["drive"])
logger = logging.getLogger(__name__)


@router.post("/api/trips/{trip_id}/start")
async def start_trip(trip_id: str, store: TripStore = Depends(get_store)):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    if trip.state != TripState.READY:
        raise HTTPException(status_code=400, detail=f"Trip must be READY to start, current state: {trip.state}")
    trip.state = TripState.ACTIVE
    await store.save(trip)
    return {"status": "active", "ws_url": f"/ws/drive/{trip_id}"}


@router.post("/api/trips/{trip_id}/skip-stop/{stop_id}")
async def skip_stop(trip_id: str, stop_id: str, store: TripStore = Depends(get_store)):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip.stops = [s for s in trip.stops if s.id != stop_id]
    await store.save(trip)
    return {"status": "stop_skipped", "remaining_stops": len(trip.stops)}


@router.post("/api/trips/{trip_id}/reroute")
async def reroute_trip(trip_id: str, store: TripStore = Depends(get_store)):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip.state = TripState.REROUTING
    await store.save(trip)
    return {"status": "rerouting"}


@router.websocket("/ws/drive/{trip_id}")
async def drive_websocket(websocket: WebSocket, trip_id: str):
    """
    WebSocket endpoint for real-time drive events.

    Accepts JSON messages with:
      { lat, lng, speed, heading, simulated: bool }

    If simulated=true and no lat/lng are meaningful, the backend
    auto-advances position along the polyline.

    Sends back DriveEvent JSON messages.
    """
    store = await get_store()
    trip = await store.get(trip_id)

    if trip is None:
        await websocket.close(code=4004, reason="Trip not found")
        return

    await websocket.accept()
    logger.info(f"[{trip_id}] WebSocket connected")

    engine = DriveEventEngine(trip)
    interpolator = None

    if trip.route_polyline:
        points = decode_polyline(trip.route_polyline)
        interpolator = PolylineInterpolator(points, trip.total_duration_s or 3600)

    try:
        while True:
            data = await websocket.receive_text()
            location = json.loads(data)

            lat = location.get("lat")
            lng = location.get("lng")
            speed = location.get("speed", 0.0)
            heading = location.get("heading", 0.0)
            simulated = location.get("simulated", False)

            # For simulated mode, use the provided coordinates directly
            # The client interpolates along the polyline and sends positions
            if lat is None or lng is None:
                if interpolator:
                    pos = interpolator.advance(1.0)
                    lat, lng = pos
                else:
                    await websocket.send_json({"type": "error", "message": "No position available"})
                    continue

            # Process location through drive event engine
            events = engine.process_location(lat, lng, speed, heading)

            # Send each event as a separate message
            for event in events:
                await websocket.send_json(event.model_dump())

            # Always send an ack with the current position
            await websocket.send_json({
                "type": "position_ack",
                "lat": lat,
                "lng": lng,
                "simulated": simulated,
            })

    except WebSocketDisconnect:
        logger.info(f"[{trip_id}] WebSocket disconnected")
    except Exception as e:
        logger.error(f"[{trip_id}] WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass
