from pydantic import BaseModel


class RankingWeights(BaseModel):
    preference: float = 0.30
    scenic: float = 0.20
    meal: float = 0.20
    timing: float = 0.15
    detour: float = 0.10
    congestion: float = 0.05


class StopScore(BaseModel):
    preference_match: float
    scenic_value: float
    meal_fit: float
    timing_fit: float
    detour_penalty: float
    congestion_penalty: float = 0.0
    total_score: float
    selection_reason: str
    weights: RankingWeights = RankingWeights()
