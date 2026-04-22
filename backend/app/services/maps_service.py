import asyncio
import hashlib
import json
import logging

import httpx

from app.models.corridor import CorridorGeometry
from app.models.trip import CandidateStop
from app.engine.geo_utils import decode_polyline, distance_along_polyline, haversine

logger = logging.getLogger(__name__)

# OSM tag → our internal type mapping
OSM_TYPE_MAP: dict[str, list[str]] = {
    "tourism=viewpoint": ["tourist_attraction", "point_of_interest", "natural_feature"],
    "tourism=attraction": ["tourist_attraction", "point_of_interest"],
    "tourism=museum": ["museum", "tourist_attraction"],
    "tourism=gallery": ["art_gallery", "tourist_attraction"],
    "natural=beach": ["beach", "natural_feature"],
    "natural=peak": ["natural_feature", "point_of_interest"],
    "natural=cliff": ["natural_feature", "point_of_interest"],
    "leisure=park": ["park"],
    "leisure=nature_reserve": ["park", "natural_feature"],
    "leisure=garden": ["park"],
    "amenity=restaurant": ["restaurant", "food"],
    "amenity=cafe": ["cafe", "food"],
    "amenity=fast_food": ["restaurant", "food"],
    "amenity=fuel": ["gas_station"],
    "amenity=place_of_worship": ["church"],
    "historic=castle": ["museum", "tourist_attraction"],
    "historic=monument": ["tourist_attraction", "point_of_interest"],
    "historic=memorial": ["tourist_attraction", "point_of_interest"],
    "shop=*": ["store"],
}


def _osm_tags_to_types(tags: dict[str, str]) -> list[str]:
    """Convert OSM tags to our internal type list."""
    types: set[str] = set()
    for osm_key, internal_types in OSM_TYPE_MAP.items():
        key, _, value = osm_key.partition("=")
        if key in tags:
            if value == "*" or tags[key] == value:
                types.update(internal_types)
    if "tourism" in tags or "historic" in tags:
        types.add("point_of_interest")
    return list(types) if types else ["point_of_interest"]


# --- Retry utility ---

async def _retry_request(
    coro_factory,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
):
    """
    Retry an async request with exponential backoff.
    coro_factory should be a callable that returns a new coroutine each call.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except httpx.HTTPStatusError as e:
            last_exc = e
            if e.response.status_code == 429:
                delay = min(base_delay * (2 ** attempt), max_delay)
                retry_after = e.response.headers.get("Retry-After")
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except ValueError:
                        pass
                logger.warning(f"Rate limited (429), retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            elif e.response.status_code >= 500:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Server error {e.response.status_code}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            else:
                raise
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            last_exc = e
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"Connection error: {e}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


# --- Geocoding cache (in-memory, persists for process lifetime) ---

_geocode_cache: dict[str, tuple[float, float]] = {}


def _cache_key(address: str) -> str:
    normalized = address.strip().lower()
    return hashlib.md5(normalized.encode()).hexdigest()


class MapsService:
    """
    Geospatial data service using open-source infrastructure:
    - OSRM (Open Source Routing Machine) for routing — no API key needed
    - Overpass API for POI search from OpenStreetMap — no API key needed
    - Nominatim for geocoding — no API key needed
    """

    OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self):
        pass

    async def _geocode(self, address: str) -> tuple[float, float]:
        """Geocode an address to (lat, lng) using Nominatim with caching."""
        key = _cache_key(address)
        if key in _geocode_cache:
            logger.debug(f"Geocode cache hit: {address}")
            return _geocode_cache[key]

        async def _do_geocode():
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    self.NOMINATIM_URL,
                    params={
                        "q": address,
                        "format": "json",
                        "limit": 1,
                    },
                    headers={"User-Agent": "TourGuideAI/0.1 (student project)"},
                )
                resp.raise_for_status()
                return resp.json()

        results = await _retry_request(_do_geocode)

        if not results:
            raise ValueError(f"Could not geocode address: {address}")

        result = (float(results[0]["lat"]), float(results[0]["lon"]))
        _geocode_cache[key] = result
        return result

    async def get_route(self, origin: str, destination: str) -> dict:
        """
        Get a driving route using OSRM (free, no API key).
        Returns dict with polyline, distance_m, duration_s.
        """
        origin_lat, origin_lng = await self._geocode(origin)
        dest_lat, dest_lng = await self._geocode(destination)

        coords = f"{origin_lng},{origin_lat};{dest_lng},{dest_lat}"

        async def _do_route():
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.OSRM_ROUTE_URL}/{coords}",
                    params={
                        "overview": "full",
                        "geometries": "polyline",
                        "steps": "false",
                    },
                )
                resp.raise_for_status()
                return resp.json()

        data = await _retry_request(_do_route)

        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError(f"OSRM routing failed: {data.get('code', 'unknown error')}")

        route = data["routes"][0]
        return {
            "polyline": route["geometry"],
            "distance_m": route["distance"],
            "duration_s": route["duration"],
        }

    async def search_places_along_corridor(
        self,
        corridor: CorridorGeometry,
        max_results: int = 80,
    ) -> list[CandidateStop]:
        """
        Search for POIs along the route corridor using Overpass API with retry.
        """
        polyline_points = decode_polyline(corridor.route_polyline)

        n = len(corridor.sample_points)
        radius_m = int(min(corridor.corridor_width_m, 10000))

        # Query 1: scenic POIs
        scenic_indices = [n * i // 6 for i in range(1, 6)]
        scenic_points = [corridor.sample_points[i] for i in scenic_indices if i < n]
        scenic_clauses = "".join(
            f'node["tourism"~"viewpoint|attraction|museum|gallery"](around:{radius_m},{cp.lat:.5f},{cp.lng:.5f});'
            f'node["natural"~"beach|peak|cliff"](around:{radius_m},{cp.lat:.5f},{cp.lng:.5f});'
            f'node["historic"~"castle|monument|memorial"](around:{radius_m},{cp.lat:.5f},{cp.lng:.5f});'
            f'way["natural"="beach"]["name"](around:{radius_m},{cp.lat:.5f},{cp.lng:.5f});'
            for cp in scenic_points
        )
        scenic_query = f'[out:json][timeout:20];({scenic_clauses});out center tags {max_results};'

        # Query 2: food stops
        food_points = [corridor.sample_points[n // 4], corridor.sample_points[n // 2], corridor.sample_points[3 * n // 4]]
        food_clauses = "".join(
            f'node["amenity"~"restaurant|cafe"]["name"](around:{radius_m},{cp.lat:.5f},{cp.lng:.5f});'
            f'node["leisure"~"park|nature_reserve"]["name"](around:{radius_m},{cp.lat:.5f},{cp.lng:.5f});'
            for cp in food_points
        )
        food_query = f'[out:json][timeout:15];({food_clauses});out center tags 30;'

        all_elements: list[dict] = []

        async with httpx.AsyncClient(timeout=45.0) as client:
            # Scenic query with retry
            async def _scenic():
                resp = await client.post(
                    self.OVERPASS_URL,
                    data={"data": scenic_query},
                    headers={"User-Agent": "TourGuideAI/0.1 (student project)"},
                )
                resp.raise_for_status()
                return resp.json()

            try:
                data = await _retry_request(_scenic)
                all_elements.extend(data.get("elements", []))
                logger.info(f"Scenic query returned {len(data.get('elements', []))} elements")
            except Exception as e:
                logger.warning(f"Scenic Overpass query failed after retries: {e}")

            await asyncio.sleep(1)

            # Food query with retry
            async def _food():
                resp = await client.post(
                    self.OVERPASS_URL,
                    data={"data": food_query},
                    headers={"User-Agent": "TourGuideAI/0.1 (student project)"},
                )
                resp.raise_for_status()
                return resp.json()

            try:
                data = await _retry_request(_food)
                all_elements.extend(data.get("elements", []))
                logger.info(f"Food query returned {len(data.get('elements', []))} elements")
            except Exception as e:
                logger.warning(f"Food Overpass query failed after retries: {e}")

        all_candidates: dict[str, CandidateStop] = {}

        for element in all_elements:
            tags = element.get("tags", {})
            name = tags.get("name")
            if not name:
                continue

            if element["type"] == "node":
                lat = element["lat"]
                lng = element["lon"]
            elif "center" in element:
                lat = element["center"]["lat"]
                lng = element["center"]["lon"]
            else:
                continue

            osm_id = f"osm_{element['type']}_{element['id']}"
            if osm_id in all_candidates:
                continue

            min_dist = float("inf")
            for cp in corridor.sample_points:
                d = haversine(lat, lng, cp.lat, cp.lng)
                if d < min_dist:
                    min_dist = d

            if min_dist > corridor.corridor_width_m:
                continue

            along_m, nearest_idx = distance_along_polyline(lat, lng, polyline_points)

            rating = None
            if "stars" in tags:
                try:
                    rating = float(tags["stars"])
                except ValueError:
                    pass

            all_candidates[osm_id] = CandidateStop(
                place_id=osm_id,
                name=name,
                lat=lat,
                lng=lng,
                types=_osm_tags_to_types(tags),
                rating=rating,
                distance_to_route_m=min_dist,
                distance_along_route_m=along_m,
                nearest_corridor_point_idx=nearest_idx,
            )

        return list(all_candidates.values())

    async def get_route_with_waypoints(
        self, origin: str, destination: str, waypoints: list[dict]
    ) -> list[dict]:
        """
        Get routes between origin → waypoints → destination using OSRM with retry.
        """
        origin_lat, origin_lng = await self._geocode(origin)
        dest_lat, dest_lng = await self._geocode(destination)

        points = [(origin_lng, origin_lat)]
        for wp in waypoints:
            points.append((wp["lng"], wp["lat"]))
        points.append((dest_lng, dest_lat))

        coords = ";".join(f"{lng},{lat}" for lng, lat in points)

        async def _do_route():
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.OSRM_ROUTE_URL}/{coords}",
                    params={
                        "overview": "full",
                        "geometries": "polyline",
                        "steps": "false",
                    },
                )
                resp.raise_for_status()
                return resp.json()

        data = await _retry_request(_do_route)

        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError(f"OSRM routing failed: {data.get('code')}")

        route = data["routes"][0]
        legs = route.get("legs", [])

        segments = []
        for leg in legs:
            segments.append({
                "polyline": route["geometry"],
                "distance_m": leg["distance"],
                "duration_s": leg["duration"],
            })

        return segments
