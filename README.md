# TourGuideAI

A full-stack road trip planning copilot that discovers interesting stops along your route using a deterministic geospatial corridor engine. Built with FastAPI (Python) and React Native (Expo).

Unlike simple radius-based searches, TourGuideAI builds a corridor along your actual driving path, scores candidate stops across multiple dimensions, and assembles an optimized itinerary with explainable rankings.

## Features

- **Geospatial Corridor Engine** — Samples points along the route polyline and builds a search corridor, ensuring stops are actually near the road you'll drive
- **Multi-Factor Stop Ranking** — Scores stops across 5 dimensions: interest relevance, rating quality, detour cost, spacing distribution, and meal timing
- **Explainable Selection** — Every stop includes a score breakdown and human-readable reason for why it was chosen
- **Live Drive Simulation** — Animated car marker follows the route with configurable speed (1x-10x), triggering events as you approach stops
- **Drive Event Engine** — Backend state machine processes GPS positions and fires events: approaching stop, arrived, missed stop, fun fact narration, segment changes
- **Trip History** — Browse and revisit previously planned trips
- **Demo Mode** — Pre-built SF to LA trip with 6 scored stops for instant demo
- **Gemini Enrichment** — Optional Google Gemini integration for stop descriptions and fun facts (graceful degradation without API key)
- **Dark Mode** — Full dark mode support across all screens
- **Cross-Platform** — Runs on iOS, Android, and Web via Expo

## Architecture

```
User → Mobile App (Expo) → FastAPI Backend → External APIs
                                  │
                                  ├── OSRM (routing)
                                  ├── Overpass (places)
                                  ├── Nominatim (geocoding)
                                  └── Gemini (enrichment, optional)
```

The backend pipeline runs 7 steps sequentially:

1. **Route** — Geocode origin/destination, fetch driving route from OSRM
2. **Corridor** — Decode polyline, sample points, build search corridor
3. **Candidates** — Query Overpass API for POIs within the corridor
4. **Ranking** — Score each candidate across 5 weighted factors
5. **Itinerary** — Select top stops with spacing/detour constraints
6. **Segments** — Fetch driving segments between consecutive stops
7. **Enrichment** — Gemini generates descriptions and fun facts (optional)

All core geospatial logic is deterministic — no LLM decisions for routing, ranking, or selection.

## Project Structure

```
backend/
├── app/
│   ├── engine/          # Core geospatial logic
│   │   ├── corridor.py      # Corridor construction from polyline
│   │   ├── ranking.py       # Multi-factor stop scoring
│   │   ├── itinerary.py     # Stop selection with constraints
│   │   ├── drive_events.py  # GPS-based event detection
│   │   ├── state_machine.py # Trip lifecycle states
│   │   └── geo_utils.py     # Haversine, bearing, polyline decode
│   ├── models/          # Pydantic data models
│   ├── routers/         # API endpoints (trips, drive, demo)
│   ├── services/        # External API integrations
│   │   ├── maps_service.py         # OSRM + Overpass + Nominatim
│   │   ├── gemini_service.py       # Google Gemini enrichment
│   │   ├── tour_assembler.py       # Pipeline orchestrator
│   │   └── polyline_interpolator.py # Server-side position interpolation
│   └── db/              # SQLite persistence
├── tests/               # 91 tests
└── data/demo/           # Pre-built demo trip data

mobile/
├── app/                 # Expo Router screens
│   ├── index.tsx            # Home: trip creation, popular routes, history
│   ├── trip/[id].tsx        # Trip review: map, stops, segments
│   ├── drive/[id].tsx       # Drive simulation: animated map, events
│   └── about.tsx            # About screen
├── components/
│   ├── map/             # Platform-split map components
│   │   ├── RouteMap.tsx         # Native: react-native-maps
│   │   ├── WebMap.tsx           # Web: Leaflet in iframe
│   │   ├── MapWrapper.native.tsx / .web.tsx  # Platform resolver
│   │   └── DriveMap.native.tsx / .web.tsx    # Drive map resolver
│   ├── trip/            # Trip review components
│   │   ├── StopCard.tsx         # Score breakdown bars
│   │   ├── SegmentTimeline.tsx  # Drive segment connector
│   │   └── PreferencesForm.tsx  # Interest/avoid chips
│   └── drive/           # Drive simulation components
│       ├── CurrentSegment.tsx   # Segment progress bar
│       ├── UpcomingStop.tsx     # Approaching stop card
│       └── FunFactPopup.tsx     # Animated fun fact overlay
├── hooks/
│   ├── useTrip.ts           # Trip polling with timeout
│   └── useDriveSocket.ts   # WebSocket with auto-reconnect
├── services/
│   ├── api.ts               # Backend API client
│   └── polyline.ts          # Client-side polyline decoder
└── types/
    └── index.ts             # Shared TypeScript interfaces
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Copy environment config
cp .env.example .env
# Edit .env — only GEMINI_API_KEY is optional, everything else works out of the box

# Run the server
uvicorn app.main:app --reload --port 8000
```

The backend uses free, open-source APIs (OSRM, Overpass, Nominatim) by default — no API keys required for core functionality.

### Mobile App

```bash
cd mobile

# Install dependencies
npm install

# Start Expo dev server
npx expo start

# For web
npx expo start --web

# For iOS simulator
npx expo start --ios

# For Android emulator
npx expo start --android
```

The app connects to `http://localhost:8000` by default.

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

91 tests covering:
- Corridor construction and geometry
- Multi-factor ranking and scoring
- Itinerary building with constraints
- Trip state machine transitions
- Drive event detection
- Maps service (geocoding, routing, caching)
- Tour assembler pipeline
- Gemini enrichment (with mocked API)
- Polyline interpolation

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/trips` | Create a new trip |
| `GET` | `/api/trips` | List all trips |
| `GET` | `/api/trips/{id}` | Get trip details |
| `POST` | `/api/trips/{id}/start` | Start drive mode |
| `WS` | `/ws/drive/{id}` | Drive simulation WebSocket |
| `GET` | `/api/demo/trip` | Load pre-built demo trip |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No | Google Gemini API key for stop enrichment |
| `GOOGLE_MAPS_API_KEY` | No | Not used (OSRM/Overpass used instead) |
| `DATABASE_URL` | No | SQLite path (default: `sqlite:///./tourguide.db`) |

## Tech Stack

**Backend:** FastAPI, Pydantic, SQLite, OSRM, Overpass API, Nominatim, Google Gemini

**Mobile:** React Native (Expo), Expo Router, react-native-maps, Leaflet (web fallback), TypeScript

## License

MIT
