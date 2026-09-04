"""Low-weight historical seasonality calculations."""
def seasonality_score(average_return: float | None, win_rate: float | None) -> float:
    if average_return is None or win_rate is None: return 0.0
    return max(-2.0, min(2.0, average_return * 10 + (win_rate - .5) * 2))
