import json
from pathlib import Path

from fastapi import APIRouter

from app.models.trip import Trip

router = APIRouter(prefix="/api/demo", tags=["demo"])

DEMO_DIR = Path(__file__).parent.parent.parent / "data" / "demo"


@router.get("/sf-to-la", response_model=Trip)
async def get_demo_trip():
    """Return a pre-built demo trip (SF → LA coastal route)."""
    data = json.loads((DEMO_DIR / "sf_to_la.json").read_text())
    return Trip.model_validate(data)
