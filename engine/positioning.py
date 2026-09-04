"""COT and retail positioning interpretation."""
def cot_score(net_position: float | None, weekly_change: float | None) -> float | None:
    if net_position is None or weekly_change is None: return None
    return max(-2.0, min(2.0, weekly_change / max(abs(net_position) * .25, 1)))
def retail_contrarian(long_pct: float | None, short_pct: float | None) -> float | None:
    if long_pct is None or short_pct is None: return None
    return max(-2.0, min(2.0, (short_pct - long_pct) / 25))
