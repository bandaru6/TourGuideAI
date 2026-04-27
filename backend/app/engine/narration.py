"""
Template-based voice narration engine.

Generates human-readable narration text for drive events.
No LLM required — uses deterministic templates.
"""

from app.models.trip import Stop


class NarrationEngine:
    """Generate narration text for various drive events."""

    def approach_narration(self, stop: Stop, distance_m: float) -> str:
        dist_km = distance_m / 1000
        type_label = stop.type.value.replace("_", " ")
        base = f"Coming up in {dist_km:.1f} kilometers: {stop.name}"
        if stop.description:
            base += f". {stop.description.split('.')[0]}."
        else:
            base += f", a {type_label}."
        base += f" Suggested visit: {stop.suggested_duration_min} minutes."
        return base

    def arrival_narration(self, stop: Stop) -> str:
        base = f"You've arrived at {stop.name}."
        if stop.fun_facts:
            base += f" Did you know? {stop.fun_facts[0].text}"
        return base

    def fun_fact_narration(self, fact_text: str) -> str:
        return f"Fun fact: {fact_text}"

    def segment_transition(
        self, from_name: str, to_name: str, duration_s: float
    ) -> str:
        minutes = int(duration_s / 60)
        if minutes > 0:
            return f"Now heading to {to_name}. Estimated drive time: {minutes} minutes."
        return f"Now heading to {to_name}."

    def reroute_narration(self, new_stop_count: int) -> str:
        return f"Route updated. You now have {new_stop_count} stops remaining."
