"""Official U.S. economic data providers."""
from __future__ import annotations

from datetime import datetime

import requests


BLS_ENDPOINT = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
BLS_SERIES = {
    "CPI (All Items)": ("CUUR0000SA0", "% change from prior release"),
    "Unemployment Rate": ("LNS14000000", "percent"),
    "Total Nonfarm Employment": ("CES0000000001", "thousands of jobs"),
}


def _value(item: dict) -> float:
    return float(item["value"].replace(",", ""))


def fetch_bls_indicators(years: int = 2) -> list[dict]:
    """Fetch the latest CPI and labor observations from the public BLS API."""
    current_year = datetime.utcnow().year
    payload = {"seriesid": [series_id for series_id, _ in BLS_SERIES.values()], "startyear": str(current_year - years), "endyear": str(current_year)}
    try:
        response = requests.post(BLS_ENDPOINT, json=payload, timeout=(5, 15))
        response.raise_for_status()
        body = response.json()
        if body.get("status") != "REQUEST_SUCCEEDED":
            return []
    except (requests.RequestException, ValueError):
        return []

    by_series = {series["seriesID"]: series.get("data", []) for series in body.get("Results", {}).get("series", [])}
    events = []
    for label, (series_id, unit) in BLS_SERIES.items():
        observations = by_series.get(series_id, [])
        if not observations:
            continue
        latest = observations[0]
        previous = observations[1] if len(observations) > 1 else None
        latest_value = _value(latest)
        previous_value = _value(previous) if previous else None
        events.append({
            "event": label,
            "value": latest_value,
            "change": latest_value - previous_value if previous_value is not None else None,
            "unit": unit,
            "period": f"{latest.get('periodName', '')} {latest.get('year', '')}",
            "timestamp": datetime.utcnow(),
            "source": "U.S. BLS",
        })
    return events


class EconomicDataProvider:
    """Provider interface backed by official BLS labor and CPI releases."""

    def events(self, currencies: list[str]) -> list[dict]:
        return fetch_bls_indicators()
