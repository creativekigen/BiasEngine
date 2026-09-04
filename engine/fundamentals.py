"""Structural macro fundamentals, separate from marginal repricing."""
def structural_score(growth: float, inflation: float, labor: float, fiscal: float, terms_of_trade: float) -> float:
    return max(-2.0, min(2.0, (growth + inflation + labor + fiscal + terms_of_trade) / 5))
