"""Public CFTC Commitments of Traders data provider."""
from __future__ import annotations

from datetime import datetime

import requests


CFTC_ENDPOINT = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
CURRENCY_MARKETS = {
    "AUD": "AUSTRALIAN DOLLAR",
    "CAD": "CANADIAN DOLLAR",
    "CHF": "SWISS FRANC",
    "EUR": "EURO FX",
    "GBP": "BRITISH POUND",
    "JPY": "JAPANESE YEN",
    "NZD": "NEW ZEALAND DOLLAR",
    "USD": "U.S. DOLLAR INDEX",
}


def _number(row: dict, field: str) -> float:
    return float(row.get(field) or 0)


def _market_rows(market: str) -> list[dict]:
    response = requests.get(
        CFTC_ENDPOINT,
        params={
            "$limit": 100,
            "$order": "report_date_as_yyyy_mm_dd DESC",
            "$where": f"upper(market_and_exchange_names) like '%{market}%'",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def fetch_cot_positions(currencies: list[str]) -> dict[str, dict]:
    """Return latest non-commercial futures positioning for each currency."""
    positions = {}
    for currency in currencies:
        market = CURRENCY_MARKETS.get(currency)
        if not market:
            continue
        try:
            rows = _market_rows(market)
            if not rows:
                continue
            latest = rows[0]
            net = _number(latest, "noncomm_positions_long_all") - _number(latest, "noncomm_positions_short_all")
            long_change = _number(latest, "change_in_noncomm_long_all")
            short_change = _number(latest, "change_in_noncomm_short_all")
            positions[currency] = {
                "net_position": net,
                "weekly_change": long_change - short_change,
                "long": _number(latest, "noncomm_positions_long_all"),
                "short": _number(latest, "noncomm_positions_short_all"),
                "report_date": latest.get("report_date_as_yyyy_mm_dd"),
                "source": "CFTC COT",
                "timestamp": datetime.utcnow(),
            }
        except (requests.RequestException, TypeError, ValueError):
            continue
    return positions


class COTProvider:
    """Compatibility wrapper for the replaceable provider interface."""

    def positions(self, currencies: list[str]) -> dict[str, dict]:
        return fetch_cot_positions(currencies)
