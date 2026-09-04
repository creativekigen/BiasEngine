"""Repricing logic: expected versus actual, guidance, and price response."""
def economic_surprise(actual: float | None, forecast: float | None, scale: float = 1.0) -> float:
    if actual is None or forecast is None: return 0.0
    return max(-2.0, min(2.0, (actual - forecast) / max(abs(scale), 1e-9)))

def central_bank_repricing(expected_hike: float, actual_hike: float, guidance_delta: float) -> float:
    return max(-2.0, min(2.0, (actual_hike - expected_hike) + guidance_delta))

def catalyst_weight(age_hours: float) -> float:
    return 1.0 if age_hours <= 24 else 0.75 if age_hours <= 48 else 0.40 if age_hours <= 168 else 0.15
