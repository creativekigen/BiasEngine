"""Pair scoring and signal gates. Repricing has more influence than rate level."""
from dataclasses import asdict
from data.models import PairAnalysis

WEIGHTS = {"macro": .20, "policy": .20, "yield": .15, "surprise": .10, "cot": .10, "retail": .05, "risk": .05, "technical": .10, "seasonality": .05}

def grade(confidence: float, score: float) -> str:
    if confidence < 45: return "NO TRADE"
    return "A+" if confidence >= 88 and score >= 75 else "A" if confidence >= 82 else "A-" if confidence >= 76 else "B+" if confidence >= 70 else "B" if confidence >= 62 else "B-" if confidence >= 55 else "C"

def score_pair(pair: str, market: dict, base: float, quote: float, factors: dict[str, float], catalyst: str, technical: float) -> PairAnalysis:
    factors = {**factors, "technical": technical}
    weighted = sum(WEIGHTS.get(key, 0) * max(-2, min(2, value)) for key, value in factors.items())
    score = max(0.0, min(100.0, 50 + weighted * 25))
    alignment = sum(1 for value in factors.values() if value > .25) if score >= 50 else sum(1 for value in factors.values() if value < -.25)
    contradictions = []
    if base > 0 and quote > 0 and technical < 0: contradictions.append("Macro direction is not confirmed by price")
    if abs(weighted) < .18: contradictions.append("Factors are insufficiently aligned")
    confidence = max(25.0, min(94.0, 48 + abs(weighted) * 22 - len(contradictions) * 10))
    action = "NO TRADE" if len(contradictions) >= 2 or confidence < 45 else "BUY" if score >= 55 else "SELL" if score <= 45 else "WAIT"
    direction = "bullish" if action == "BUY" else "bearish" if action == "SELL" else "neutral"
    return PairAnalysis(pair, market.get("price"), market.get("daily_change"), round(score, 1), direction, round(confidence, 1), grade(confidence, score), {k: round(v, 2) for k, v in factors.items()}, alignment, catalyst, action, f"Marginal repricing and cross-asset flow are {direction}; price confirmation is {technical:+.1f}.", contradictions)

def analyze_all(market: dict, currency: dict, catalysts: list[dict]) -> list[PairAnalysis]:
    result = []
    for pair in market:
        base, quote = pair[:3], pair[3:]
        b, q = currency.get(base, {}), currency.get(quote, {})
        factors = {"macro": b.get("structural", 0) - q.get("structural", 0), "policy": b.get("repricing", 0) - q.get("repricing", 0), "yield": b.get("repricing", 0) - q.get("repricing", 0), "surprise": b.get("repricing", 0) - q.get("repricing", 0), "cot": 0, "retail": 0, "risk": 0, "seasonality": 0}
        tech = 2 if market[pair]["daily_change"] > .35 else -2 if market[pair]["daily_change"] < -.35 else 0
        catalyst = next((c["event"] for c in catalysts if c["currency"] in (base, quote)), "No fresh catalyst")
        result.append(score_pair(pair, market[pair], b.get("structural", 0) - q.get("structural", 0), q.get("structural", 0), factors, catalyst, tech))
    return result
