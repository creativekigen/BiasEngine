"""Cross-asset correlation helpers."""
def rolling_correlation(left, right, window: int = 60):
    return left.rolling(window).corr(right)
