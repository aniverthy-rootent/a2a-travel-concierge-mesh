"""Geo Agent - resolves a place name to coordinates, country, timezone and currency (Open-Meteo geocoding)."""
import httpx

PORT = 9101
NAME = "Geo Agent"
DESCRIPTION = "Resolves a place name to coordinates, country, timezone and local currency."
SKILLS = [{"id": "geocode", "name": "Geocode a place", "description": "input {place}; output lat/lon/country/timezone/currency",
           "tags": ["geo", "location"]}]


def handle(data: dict) -> dict:
    place = data["place"]
    r = httpx.get("https://geocoding-api.open-meteo.com/v1/search",
                  params={"name": place, "count": 1, "language": "en", "format": "json"}, timeout=20)
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        raise ValueError(f"place not found: {place}")
    hit = results[0]
    currency = None
    try:  # restcountries gives the local currency
        c = httpx.get(f"https://restcountries.com/v3.1/alpha/{hit['country_code']}", params={"fields": "currencies"}, timeout=20)
        currency = next(iter(c.json()[0]["currencies"])) if c.status_code == 200 else None
    except (httpx.HTTPError, KeyError, IndexError, StopIteration):
        pass
    return {"name": hit["name"], "country": hit.get("country"), "country_code": hit.get("country_code"),
            "admin1": hit.get("admin1"), "latitude": hit["latitude"], "longitude": hit["longitude"],
            "timezone": hit.get("timezone"), "population": hit.get("population"), "local_currency": currency}
