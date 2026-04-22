from fastapi import APIRouter

router = APIRouter(prefix="/api/spotify", tags=["spotify"])


@router.get("/status")
async def spotify_status():
    return {"connected": False, "message": "Spotify integration coming in Phase 6"}
