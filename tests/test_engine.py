from engine.repricing import central_bank_repricing, economic_surprise, catalyst_weight
from engine.scoring import analyze_all
from data.seed_data import demo_market, demo_currency, demo_catalysts


def test_expected_hike_with_dovish_guidance_is_bearish_repricing():
    assert central_bank_repricing(.25, .25, -.8) < 0


def test_unchanged_rate_with_hawkish_guidance_is_bullish_repricing():
    assert central_bank_repricing(0, 0, .8) > 0


def test_surprise_is_actual_minus_forecast():
    assert economic_surprise(105, 100, 5) == 1


def test_catalyst_freshness_decays():
    assert catalyst_weight(12) > catalyst_weight(72) > catalyst_weight(240)


def test_all_28_pairs_are_scored():
    analyses = analyze_all(demo_market(), demo_currency(), demo_catalysts())
    assert len(analyses) == 28
    assert all(a.action in {"BUY", "SELL", "WAIT", "NO TRADE"} for a in analyses)
