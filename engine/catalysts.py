"""Fresh catalyst weights and override logic."""
from .repricing import catalyst_weight
def override(surprise: float, age_hours: float, importance: int) -> float:
    return max(-2.0, min(2.0, surprise * catalyst_weight(age_hours) * min(1.0, importance / 5)))
