"""Signal gates and contradiction checks."""
def contradictions(factors: dict[str, float]) -> list[str]:
    positive = sum(v > .25 for v in factors.values()); negative = sum(v < -.25 for v in factors.values())
    return ["Major factor contradiction"] if positive >= 3 and negative >= 3 else []
def signal_gate(factors: dict[str, float], data_complete: bool) -> str:
    if not data_complete or contradictions(factors): return "NO TRADE"
    return "READY" if sum(v > .25 for v in factors.values()) >= 5 or sum(v < -.25 for v in factors.values()) >= 5 else "WAIT"
