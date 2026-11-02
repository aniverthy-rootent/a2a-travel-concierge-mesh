"""Weather Agent - real forecast (next 14 days) or last year's same-dates climate (Open-Meteo)."""
from datetime import date, timedelta

import httpx

PORT = 9102
NAME = "Weather Agent"
DESCRIPTION = "Daily weather for a trip: live forecast if the trip is within 14 days, otherwise the same dates last year."
SKILLS = [{"id": "trip_weather", "name": "Trip weather", "description": "input {latitude, longitude, start_date, days}",
           "tags": ["weather", "forecast", "climate"]}]
DAILY = "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"


def handle(data: dict) -> dict:
    lat, lon, days = data["latitude"], data["longitude"], int(data.get("days", 4))
    start = date.fromisoformat(data["start_date"])
    end = start + timedelta(days=days - 1)
    if start <= date.today() + timedelta(days=13):
        url, kind = "https://api.open-meteo.com/v1/forecast", "forecast"
        s, e = start, min(end, date.today() + timedelta(days=15))
    else:
        url, kind = "https://archive-api.open-meteo.com/v1/archive", "historical (same dates last year)"
        s, e = start.replace(year=start.year - 1), end.replace(year=end.year - 1)
        if e >= date.today():
            s, e = s.replace(year=s.year - 1), e.replace(year=e.year - 1)
    r = httpx.get(url, params={"latitude": lat, "longitude": lon, "start_date": s.isoformat(), "end_date": e.isoformat(),
                               "daily": DAILY, "timezone": "auto"}, timeout=30)
    r.raise_for_status()
    d = r.json()["daily"]
    rows = [{"date": d["time"][i], "max_c": d["temperature_2m_max"][i], "min_c": d["temperature_2m_min"][i],
             "rain_mm": d["precipitation_sum"][i], "wmo_code": d["weathercode"][i]} for i in range(len(d["time"]))]
    rainy = sum(1 for x in rows if (x["rain_mm"] or 0) >= 1)
    avg_hi = round(sum(x["max_c"] for x in rows) / len(rows), 1) if rows else None
    return {"source": kind, "days": rows, "rainy_days": rainy, "avg_high_c": avg_hi}
