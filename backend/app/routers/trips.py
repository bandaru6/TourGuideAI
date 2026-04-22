from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.config import Settings
from app.db.store import TripStore
from app.dependencies import get_settings, get_store
from app.models.preferences import UserPreferences
from app.models.trip import Trip, Stop
from app.models.drive_events import TripState
from app.services.tour_assembler import TourAssembler

router = APIRouter(prefix="/api/trips", tags=["trips"])


class CreateTripRequest(BaseModel):
    origin: str
    destination: str
    preferences: UserPreferences = UserPreferences()
    departure_time: str | None = None


@router.post("", response_model=Trip)
async def create_trip(
    req: CreateTripRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    store: TripStore = Depends(get_store),
):
    # Validate inputs
    if not req.origin.strip():
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_ORIGIN", "message": "Origin address is required"},
        )
    if not req.destination.strip():
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_DESTINATION", "message": "Destination address is required"},
        )

    trip = Trip(
        origin=req.origin.strip(),
        destination=req.destination.strip(),
        preferences=req.preferences,
        state=TripState.GENERATING,
        departure_time=req.departure_time,
    )
    await store.save(trip)

    assembler = TourAssembler(settings)
    background_tasks.add_task(assembler.generate_trip, trip, store)

    return trip


class TripSummary(BaseModel):
    id: str
    origin: str
    destination: str
    state: str
    total_distance_m: float
    total_duration_s: float
    stops_count: int


@router.get("", response_model=list[TripSummary])
async def list_trips(limit: int = 20, store: TripStore = Depends(get_store)):
    """List recent trips with summary info."""
    trips = await store.list_trips(limit=limit)
    return [
        TripSummary(
            id=t.id,
            origin=t.origin,
            destination=t.destination,
            state=t.state.value if hasattr(t.state, "value") else str(t.state),
            total_distance_m=t.total_distance_m,
            total_duration_s=t.total_duration_s,
            stops_count=len(t.stops),
        )
        for t in trips
    ]


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(trip_id: str, store: TripStore = Depends(get_store)):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@router.get("/{trip_id}/stops", response_model=list[Stop])
async def get_trip_stops(trip_id: str, store: TripStore = Depends(get_store)):
    trip = await store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.stops
