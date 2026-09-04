"""Explainable technical indicators."""
import numpy as np

def technical_score(closes: list[float]) -> dict:
    if len(closes) < 14:
        return {"score": 0.0, "rsi": None, "sma3": None, "sma14": None, "status": "UNAVAILABLE"}
    values = np.asarray(closes, dtype=float)
    sma3, sma14 = values[-3:].mean(), values[-14:].mean()
    gains = np.maximum(np.diff(values), 0)
    losses = np.maximum(-np.diff(values), 0)
    rs = gains[-14:].mean() / max(losses[-14:].mean(), 1e-9)
    rsi = 100 - (100 / (1 + rs))
    score = 2.0 if values[-1] > sma14 and sma3 > sma14 else -2.0 if values[-1] < sma14 and sma3 < sma14 else 0.0
    return {"score": score, "rsi": round(float(rsi), 1), "sma3": float(sma3), "sma14": float(sma14), "status": "DEMO"}
