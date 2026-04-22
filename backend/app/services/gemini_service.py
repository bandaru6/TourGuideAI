import json
import logging

import httpx

from app.models.trip import Trip, FunFact

logger = logging.getLogger(__name__)


class GeminiService:
    """LLM enrichment service using Google Gemini API.

    Generates fun facts and stop descriptions. Degrades gracefully
    when no API key is configured — returns trip unchanged.
    """

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.enabled = bool(api_key)

    async def enrich_trip(self, trip: Trip) -> Trip:
        """Enrich trip stops with descriptions and fun facts."""
        if not self.enabled:
            logger.info("Gemini API key not configured, skipping enrichment")
            return trip

        if not trip.stops:
            return trip

        try:
            return await self._do_enrich(trip)
        except Exception as e:
            logger.warning(f"Gemini enrichment failed, continuing without: {e}")
            return trip

    async def _do_enrich(self, trip: Trip) -> Trip:
        stop_names = [s.name for s in trip.stops]
        prompt = self._build_prompt(trip.origin, trip.destination, stop_names)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.API_URL}?key={self.api_key}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2048,
                        "responseMimeType": "application/json",
                    },
                },
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        # Extract generated text
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        enrichments = json.loads(text)

        # Apply enrichments to stops
        for stop in trip.stops:
            enrichment = enrichments.get(stop.name, {})
            if enrichment.get("description"):
                stop.description = enrichment["description"]

            for fact_text in enrichment.get("fun_facts", []):
                stop.fun_facts.append(
                    FunFact(
                        text=fact_text,
                        trigger_lat=stop.lat,
                        trigger_lng=stop.lng,
                        trigger_distance_along_route_m=stop.distance_along_route_m,
                        radius_m=2000,
                    )
                )

        return trip

    def _build_prompt(self, origin: str, destination: str, stop_names: list[str]) -> str:
        stops_list = "\n".join(f"- {name}" for name in stop_names)
        return f"""You are a knowledgeable travel guide. For a road trip from {origin} to {destination}, provide enrichment for each stop.

Stops:
{stops_list}

Return a JSON object where each key is the stop name, and each value has:
- "description": A 1-2 sentence engaging description of the place
- "fun_facts": An array of 1-2 interesting fun facts about the location

Example format:
{{
  "Stop Name": {{
    "description": "A beautiful coastal viewpoint...",
    "fun_facts": ["This spot was featured in...", "The local wildlife includes..."]
  }}
}}

Only include the JSON, no other text."""
