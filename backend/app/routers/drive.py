import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.db.store import TripStore
from app.dependencies import get_store, get_settings
from app.config import Settings
from app.engine.command_parser import CommandType, VoiceCommandRequest, parse_command
from app.engine.drive_events import DriveEventEngine
from app.engine.geo_utils import decode_polyline
from app.engine.narration import NarrationEngine
from app.engine.traffic import apply_traffic_to_segments, suggest_drops
from app.models.drive_events import DriveEvent, DriveEventType, TripState
from app.services.maps_service import MapsService
from app.services.gemini_service import GeminiService
from app.services.polyline_interpolator import PolylineInterpolator
from app.services.reroute_service import RerouteService

router = APIRouter(tags=["drive"])
logger = logging.getLogger(__name__)


class SkipStopRequest(BaseModel):
    lat: float | None = None
    lng: float | None = None


class RerouteRequest(BaseModel):
    lat: float | None = None
    lng: float | None = None


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
async def skip_stop(
    trip_id: str,
    stop_id: str,
    body: SkipStopRequest | None = None,
    store: TripStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    if body and body.lat is not None and body.lng is not None:
        # Lightweight replan with reroute service
        maps = MapsService()
        reroute = RerouteService(maps)
        trip = await reroute.handle_skip_and_replan(
            trip, stop_id, body.lat, body.lng, visited_stop_ids=[]
        )
    else:
        trip.stops = [s for s in trip.stops if s.id != stop_id]

    await store.save(trip)
    return {"status": "stop_skipped", "remaining_stops": len(trip.stops)}


@router.post("/api/trips/{trip_id}/reroute")
async def reroute_trip(
    trip_id: str,
    body: RerouteRequest | None = None,
    store: TripStore = Depends(get_store),
    settings: Settings = Depends(get_settings),
):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    if body and body.lat is not None and body.lng is not None:
        trip.state = TripState.REROUTING
        await store.save(trip)

        maps = MapsService()
        gemini = GeminiService(settings.gemini_api_key)
        reroute = RerouteService(maps, gemini)
        trip = await reroute.reroute_from_position(
            trip, body.lat, body.lng, visited_stop_ids=[]
        )
        trip.state = TripState.ACTIVE
        await store.save(trip)
        return {"status": "rerouted", "stops": len(trip.stops)}
    else:
        trip.state = TripState.REROUTING
        await store.save(trip)
        return {"status": "rerouting"}


@router.post("/api/trips/{trip_id}/voice-command")
async def voice_command(
    trip_id: str,
    body: VoiceCommandRequest,
    store: TripStore = Depends(get_store),
):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    parsed = parse_command(body.transcript)
    narration = NarrationEngine()
    response_text = ""

    if parsed.type == CommandType.SKIP_STOP:
        if trip.stops:
            skipped = trip.stops[0]
            trip.stops = trip.stops[1:]
            await store.save(trip)
            response_text = f"Skipping {skipped.name}. {len(trip.stops)} stops remaining."
        else:
            response_text = "No stops to skip."

    elif parsed.type == CommandType.FIND_FOOD:
        food_stops = [s for s in trip.stops if s.type.value in ("restaurant", "cafe")]
        if food_stops:
            response_text = f"Next food stop: {food_stops[0].name}, {food_stops[0].detour_distance_m / 1000:.1f} km detour."
        else:
            response_text = "No food stops on your current route."

    elif parsed.type == CommandType.FIND_GAS:
        gas_stops = [s for s in trip.stops if s.type.value in ("gas_station", "charging")]
        if gas_stops:
            response_text = f"Nearest fuel: {gas_stops[0].name}."
        else:
            response_text = "No gas stations on your current route."

    elif parsed.type == CommandType.DISTANCE_NEXT:
        if trip.stops:
            response_text = f"Next stop is {trip.stops[0].name}, approximately {trip.stops[0].distance_along_route_m / 1000:.1f} kilometers ahead."
        else:
            response_text = "No more stops ahead."

    elif parsed.type == CommandType.ETA_DESTINATION:
        total_min = int(trip.total_duration_s / 60) if trip.total_duration_s else 0
        hours = total_min // 60
        mins = total_min % 60
        if hours > 0:
            response_text = f"Estimated arrival in {hours} hours and {mins} minutes."
        else:
            response_text = f"Estimated arrival in {mins} minutes."

    elif parsed.type == CommandType.PAUSE_NARRATION:
        response_text = "Narration paused."

    elif parsed.type == CommandType.RESUME_NARRATION:
        response_text = "Narration resumed."

    else:
        response_text = "Sorry, I didn't understand that command."

    return {
        "command": parsed.type.value,
        "confidence": parsed.confidence,
        "response_text": response_text,
    }


@router.websocket("/ws/drive/{trip_id}")
async def drive_websocket(websocket: WebSocket, trip_id: str):
    """
    WebSocket endpoint for real-time drive events.

    Accepts JSON messages with:
      { lat, lng, speed, heading, simulated: bool }

    Sends back DriveEvent JSON messages, including narration and traffic updates.
    """
    store = await get_store()
    trip = await store.get(trip_id)

    if trip is None:
        await websocket.close(code=4004, reason="Trip not found")
        return

    await websocket.accept()
    logger.info(f"[{trip_id}] WebSocket connected")

    engine = DriveEventEngine(trip)
    narration = NarrationEngine()
    interpolator = None
    tick_count = 0

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

            if lat is None or lng is None:
                if interpolator:
                    pos = interpolator.advance(1.0)
                    lat, lng = pos
                else:
                    await websocket.send_json({"type": "error", "message": "No position available"})
                    continue

            # Process location through drive event engine
            events = engine.process_location(lat, lng, speed, heading)

            # Append narration text events
            for event in list(events):
                if event.type == DriveEventType.APPROACHING_STOP:
                    stop = next((s for s in trip.stops if s.id == event.stop_id), None)
                    if stop:
                        text = narration.approach_narration(stop, event.data.get("distance_m", 2000))
                        events.append(DriveEvent(
                            type=DriveEventType.NARRATION_TEXT,
                            message=text, lat=lat, lng=lng,
                        ))
                elif event.type == DriveEventType.ENTERED_REGION:
                    stop = next((s for s in trip.stops if s.id == event.stop_id), None)
                    if stop:
                        text = narration.arrival_narration(stop)
                        events.append(DriveEvent(
                            type=DriveEventType.NARRATION_TEXT,
                            message=text, lat=lat, lng=lng,
                        ))
                elif event.type == DriveEventType.NARRATION_TRIGGER:
                    text = narration.fun_fact_narration(event.message)
                    events.append(DriveEvent(
                        type=DriveEventType.NARRATION_TEXT,
                        message=text, lat=lat, lng=lng,
                    ))
                elif event.type == DriveEventType.SEGMENT_CHANGED:
                    seg_idx = engine.current_segment_idx
                    if seg_idx < len(trip.segments):
                        seg = trip.segments[seg_idx]
                        text = narration.segment_transition(seg.from_name, seg.to_name, seg.duration_s)
                        events.append(DriveEvent(
                            type=DriveEventType.NARRATION_TEXT,
                            message=text, lat=lat, lng=lng,
                        ))

            # ETA update every 10 ticks
            tick_count += 1
            if tick_count % 10 == 0 and trip.segments:
                remaining_s = sum(
                    s.adjusted_duration_s or s.duration_s
                    for s in trip.segments[engine.current_segment_idx:]
                )
                events.append(DriveEvent(
                    type=DriveEventType.ETA_UPDATE,
                    message=f"ETA: {int(remaining_s / 60)} minutes",
                    lat=lat, lng=lng,
                    data={"remaining_s": remaining_s},
                ))

                # Schedule compression check: >20% behind
                if trip.adjusted_total_duration_s > 0:
                    expected_fraction = tick_count / max(1, trip.total_duration_s)
                    actual_remaining = remaining_s
                    expected_remaining = trip.adjusted_total_duration_s * (1 - expected_fraction)
                    if expected_remaining > 0 and actual_remaining > expected_remaining * 1.2:
                        behind_s = actual_remaining - expected_remaining
                        drops = suggest_drops(trip.stops, behind_s)
                        if drops:
                            drop_names = [d.name for d in drops]
                            events.append(DriveEvent(
                                type=DriveEventType.SCHEDULE_COMPRESSION,
                                message=f"Running behind schedule. Consider skipping: {', '.join(drop_names)}",
                                lat=lat, lng=lng,
                                data={"behind_s": behind_s, "suggested_drops": drop_names},
                            ))

            # Handle reroute events
            for event in list(events):
                if event.type == DriveEventType.REROUTE_NEEDED:
                    try:
                        maps = MapsService()
                        reroute_svc = RerouteService(maps)
                        visited = list(engine.triggered_stop_ids)
                        trip = await reroute_svc.reroute_from_position(
                            trip, lat, lng, visited
                        )
                        engine = DriveEventEngine(trip)
                        await store.save(trip)
                        text = narration.reroute_narration(len(trip.stops))
                        events.append(DriveEvent(
                            type=DriveEventType.REROUTE_COMPLETE,
                            message="Route recalculated",
                            lat=lat, lng=lng,
                            data={"new_stop_count": len(trip.stops)},
                        ))
                        events.append(DriveEvent(
                            type=DriveEventType.NARRATION_TEXT,
                            message=text, lat=lat, lng=lng,
                        ))
                    except Exception as e:
                        logger.error(f"[{trip_id}] Auto-reroute failed: {e}")

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
