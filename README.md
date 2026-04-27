# TourGuideAI

A full-stack road trip planning copilot that discovers interesting stops along your route using a deterministic geospatial corridor engine. Built with FastAPI (Python) and React Native (Expo).

Unlike simple radius-based searches, TourGuideAI builds a corridor along your actual driving path, scores candidate stops across multiple dimensions, and assembles an optimized itinerary with explainable rankings — then guides you in real time with voice narration, traffic-aware ETAs, and on-the-fly rerouting.

## Features

### Core Engine
- **Geospatial Corridor Engine** — Samples points along the route polyline and builds a search corridor, ensuring stops are actually near the road you'll drive
- **Multi-Factor Stop Ranking** — Scores stops across 6 dimensions: interest relevance, scenic value, meal timing, spacing, detour cost, and traffic congestion
- **Spatial Clustering** — Grid-based deduplication merges nearby POI candidates into representative stops, showing cluster counts
- **Constraint Solver** — Beam search optimizer respects time windows (opening hours), per-stop detour limits, and EV charging range constraints
- **Explainable Selection** — Every stop includes a score breakdown and human-readable reason for why it was chosen

### Real-Time Drive
- **Live Drive Simulation** — Animated car marker follows the route with configurable speed (1x-10x), triggering events as you approach stops
- **Traffic-Aware ETAs** — Deterministic rush-hour heuristic adjusts segment durations; schedule compression alerts suggest stops to drop when running behind
- **Real-Time Rerouting** — Full re-plan from current GPS position when off-corridor, or lightweight replan on stop skip
- **Drive Event Engine** — Backend state machine processes GPS positions and fires events: approaching stop, arrived, missed stop, fun fact narration, segment changes, ETA updates, reroute completion

### Voice
- **Voice Narration (TTS)** — Template-based narration for approaching stops, arrivals, fun facts, and segment transitions via expo-speech
- **Voice Commands** — Deterministic keyword-matching command parser: "skip this stop", "find food", "how far to next stop", "ETA", "mute"

### Polish
- **EV Mode** — Toggle EV vehicle with range input; constraint solver auto-inserts charging stops
- **Trip History** — Browse and revisit previously planned trips
- **Demo Mode** — Pre-built SF to LA trip with 6 scored stops, traffic data, and arrival times for instant demo
- **Gemini Enrichment** — Optional Google Gemini integration for stop descriptions and fun facts (graceful degradation without API key)
- **Dark Mode** — Full dark mode support across all screens
- **Cross-Platform** — Runs on iOS, Android, and Web via Expo

## Architecture

```
User → Mobile App (Expo) → FastAPI Backend → External APIs
                                  │
                                  ├── OSRM (routing)
                                  ├── Overpass (places + EV chargers)
                                  ├── Nominatim (geocoding)
                                  └── Gemini (enrichment, optional)
```

The backend pipeline runs 9 steps sequentially:

1. **Route** — Geocode origin/destination, fetch driving route from OSRM
2. **Corridor** — Decode polyline, sample points, build search corridor
3. **Candidates** — Query Overpass API for POIs within the corridor
4. **Clustering** — Grid-based spatial clustering + name deduplication
5. **Ranking** — Score each candidate across 6 weighted factors (with real congestion estimates)
6. **Itinerary** — Beam search constraint solver with time windows, EV charging, detour limits (greedy fallback)
7. **Segments** — Fetch driving segments between consecutive stops
8. **Traffic** — Apply time-of-day congestion adjustments to segment durations
9. **Enrichment** — Gemini generates descriptions and fun facts (optional)

All core geospatial logic is deterministic — no LLM decisions for routing, ranking, or selection.

## Project Structure

```
backend/
├── app/
│   ├── engine/              # Core geospatial logic (deterministic)
│   │   ├── corridor.py          # Corridor construction from polyline
│   │   ├── ranking.py           # Multi-factor stop scoring
│   │   ├── itinerary.py         # Greedy stop selection (fallback)
│   │   ├── constraint_solver.py # Beam search with time windows + EV charging
│   │   ├── clustering.py        # Grid-based spatial clustering + dedup
│   │   ├── traffic.py           # Rush-hour congestion heuristic + schedule compression
│   │   ├── narration.py         # Template-based TTS narration engine
│   │   ├── command_parser.py    # Keyword-matching voice command parser
│   │   ├── drive_events.py      # GPS-based event detection
│   │   ├── state_machine.py     # Trip lifecycle states
│   │   └── geo_utils.py         # Haversine, bearing, polyline decode
│   ├── models/              # Pydantic data models
│   ├── routers/             # API endpoints (trips, drive, demo)
│   ├── services/            # External API integrations
│   │   ├── maps_service.py          # OSRM + Overpass + Nominatim + EV chargers
│   │   ├── gemini_service.py        # Google Gemini enrichment
│   │   ├── tour_assembler.py        # Pipeline orchestrator
│   │   ├── reroute_service.py       # Real-time rerouting (full + lightweight)
│   │   └── polyline_interpolator.py # Server-side position interpolation
│   └── db/                  # SQLite persistence
├── tests/                   # 123 tests
└── data/demo/               # Pre-built demo trip data

mobile/
├── app/                     # Expo Router screens
│   ├── index.tsx                # Home: trip creation, popular routes, history
│   ├── trip/[id].tsx            # Trip review: map, stops, segments
│   ├── drive/[id].tsx           # Drive: simulation, voice, reroute, traffic
│   └── about.tsx                # About screen
├── components/
│   ├── map/                 # Platform-split map components
│   ├── trip/                # Trip review components
│   │   ├── StopCard.tsx         # Score breakdown + cluster count + arrival time
│   │   ├── SegmentTimeline.tsx  # Drive segment connector
│   │   └── PreferencesForm.tsx  # Interest/avoid chips + EV Mode toggle
│   └── drive/               # Drive simulation components
│       ├── CurrentSegment.tsx   # Segment progress + traffic indicator
│       ├── UpcomingStop.tsx     # Approaching stop card
│       ├── FunFactPopup.tsx     # Animated fun fact overlay
│       ├── NarrationControl.tsx # Speaker mute/unmute toggle
│       └── VoiceInputButton.tsx # Mic button with pulse animation
├── hooks/
│   ├── useTrip.ts               # Trip polling with timeout
│   ├── useDriveSocket.ts        # WebSocket with auto-reconnect
│   ├── useNarrationQueue.ts     # Queue-based TTS via expo-speech
│   └── useVoiceInput.[web|native].ts # Platform-split speech recognition
├── services/
│   ├── api.ts                   # Backend API client
│   └── polyline.ts              # Client-side polyline decoder
└── types/
    └── index.ts                 # Shared TypeScript interfaces
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

123 tests covering:
- Corridor construction and geometry
- Multi-factor ranking and scoring
- Itinerary building with constraints
- Constraint solver (time windows, EV charging, beam search)
- Spatial clustering and deduplication
- Traffic congestion estimation and schedule compression
- Voice command parsing
- Template-based narration
- Real-time rerouting
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
| `GET` | `/api/trips/{id}/stops` | Get stops for a trip |
| `POST` | `/api/trips/{id}/start` | Start drive mode |
| `POST` | `/api/trips/{id}/skip-stop/{stop_id}` | Skip a stop (optional `lat`, `lng` for replan) |
| `POST` | `/api/trips/{id}/reroute` | Reroute from position (`lat`, `lng`) |
| `POST` | `/api/trips/{id}/voice-command` | Parse voice transcript and execute action |
| `WS` | `/ws/drive/{id}` | Drive simulation WebSocket |
| `GET` | `/api/demo/sf-to-la` | Load pre-built demo trip |
| `GET` | `/api/health` | Health check |

### WebSocket Events

The drive WebSocket sends these event types:

| Event | Description |
|-------|-------------|
| `approaching_stop` | Within 2km of a stop |
| `entered_region` | Arrived at stop (within 200m) |
| `narration_trigger` | Fun fact triggered by GPS proximity |
| `narration_text` | TTS narration text for the client to speak |
| `missed_stop` | Passed a stop without visiting |
| `segment_changed` | Moved to next route segment |
| `eta_update` | Updated ETA (every 10 GPS ticks) |
| `schedule_compression` | Behind schedule; suggests stops to drop |
| `reroute_needed` | Off corridor; auto-reroute triggered |
| `reroute_complete` | Reroute finished; new trip data available |

### Voice Commands

| Command | Trigger Phrases |
|---------|----------------|
| Skip stop | "skip this stop", "skip", "next stop" |
| Find food | "find food", "hungry", "restaurant" |
| Find gas | "find gas", "fuel", "charging station" |
| Distance to next | "how far", "distance next" |
| ETA | "when arrive", "how long left", "eta" |
| Mute narration | "mute", "quiet", "stop talking" |
| Resume narration | "unmute", "speak", "start talking" |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | No | Google Gemini API key for stop enrichment |
| `GOOGLE_MAPS_API_KEY` | No | Not used (OSRM/Overpass used instead) |
| `DATABASE_URL` | No | SQLite path (default: `sqlite:///./tourguide.db`) |

## Tech Stack

**Backend:** FastAPI, Pydantic, SQLite, OSRM, Overpass API, Nominatim, Google Gemini

**Mobile:** React Native (Expo), Expo Router, expo-speech, react-native-maps, Leaflet (web fallback), TypeScript

**CI:** GitHub Actions (pytest + TypeScript type check)

## License

MIT
