"""Commodity impact is contextual, not a one-variable directional rule."""
def commodity_impact(change: float, surprise: float, volatility: float) -> float:
    return max(-2.0, min(2.0, change * .4 + surprise * .5 - volatility * .1))
