"""CFTC/COT provider contract. Missing data remains unavailable."""
class COTProvider:
    def positions(self, currencies: list[str]) -> dict: return {}
