from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.dependencies import get_settings, get_store
from app.routers import trips, drive, spotify, demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = await get_store()
    yield


app = FastAPI(title="TourGuideAI", version="0.1.0", lifespan=lifespan)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:8081",   # Expo dev server
        "http://localhost:19006",  # Expo web
        "exp://localhost:8081",    # Expo Go
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips.router)
app.include_router(drive.router)
app.include_router(spotify.router)
app.include_router(demo.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
