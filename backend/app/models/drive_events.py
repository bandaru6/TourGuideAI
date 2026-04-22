from enum import Enum
from pydantic import BaseModel


class TripState(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    ACTIVE = "active"
    APPROACHING_STOP = "approaching_stop"
    AT_STOP = "at_stop"
    RESUMED = "resumed"
    REROUTING = "rerouting"
    COMPLETED = "completed"


class DriveEventType(str, Enum):
    APPROACHING_STOP = "approaching_stop"
    ENTERED_REGION = "entered_region"
    NARRATION_TRIGGER = "narration_trigger"
    MISSED_STOP = "missed_stop"
    REROUTE_NEEDED = "reroute_needed"
    SEGMENT_CHANGED = "segment_changed"
    PLAYLIST_CHANGE = "playlist_change"


class DriveEvent(BaseModel):
    type: DriveEventType
    stop_id: str | None = None
    message: str = ""
    data: dict = {}
    lat: float | None = None
    lng: float | None = None
