"""Multi-asset risk regime classifier."""
def classify(vix: float, equity_change: float, gold_change: float, btc_change: float) -> dict:
    score = equity_change + btc_change * .25 - max(vix - 18, 0) * .2
    label = "STRONG RISK ON" if score > 1.2 else "RISK ON" if score > .3 else "STRONG RISK OFF" if score < -1.2 else "RISK OFF" if score < -.3 else "MIXED"
    return {"label": label, "score": round(score, 2), "contradiction": gold_change > .8 and score > .3}
