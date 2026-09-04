"""Risk and sentiment factor utilities."""
def sentiment_score(vix_change: float, equities_change: float, defensive_change: float) -> float:
    return max(-2.0, min(2.0, equities_change - vix_change - defensive_change))
