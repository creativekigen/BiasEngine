"""U.S. Treasury daily par yield curve provider."""
from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree

import requests


TREASURY_ENDPOINT = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml"
TENORS = ("1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y")


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def fetch_treasury_curve() -> dict:
    """Return the latest Treasury par curve and its previous observation."""
    response = requests.get(
        TREASURY_ENDPOINT,
        params={"data": "daily_treasury_yield_curve", "field_tdr_date_value": datetime.utcnow().year},
        timeout=15,
    )
    response.raise_for_status()
    root = ElementTree.fromstring(response.content)
    observations = []
    for entry in root.iter():
        if _local_name(entry.tag) != "entry":
            continue
        values = {_local_name(child.tag): child.text for child in entry.iter() if child.text}
        date = values.get("NEW_DATE") or values.get("Date")
        curve = {tenor: values.get(f"BC_{tenor}") for tenor in TENORS}
        if date and any(value not in (None, "") for value in curve.values()):
            observations.append((date[:10], curve))
    if not observations:
        return {}
    observations.sort(key=lambda item: item[0])
    date, curve = observations[-1]
    previous = observations[-2][1] if len(observations) > 1 else {}
    return {
        "date": date,
        "curve": {tenor: float(value) for tenor, value in curve.items() if value not in (None, "")},
        "change": {
            tenor: float(curve[tenor]) - float(previous[tenor])
            for tenor in TENORS
            if curve.get(tenor) not in (None, "") and previous.get(tenor) not in (None, "")
        },
        "source": "U.S. TREASURY",
    }


class YieldProvider:
    """Compatibility wrapper for the replaceable provider interface."""

    def curves(self, currencies: list[str]) -> dict:
        return fetch_treasury_curve()
