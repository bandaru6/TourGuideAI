from pydantic import BaseModel


class UserPreferences(BaseModel):
    interests: list[str] = []
    avoid_types: list[str] = []
    max_detour_min: int = 20
    meal_times: list[str] = ["12:00", "18:00"]
    stop_interval_min: int = 90
    stop_interval_max: int = 180
    scenic_priority: float = 0.5
    free_text: str = ""
