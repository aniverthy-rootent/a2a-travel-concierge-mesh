"""Guide Agent - nearby points of interest from Wikipedia (geosearch + page summaries)."""
import httpx

PORT = 9104
NAME = "Guide Agent"
DESCRIPTION = "Finds notable places near a coordinate and returns short Wikipedia summaries."
SKILLS = [{"id": "attractions", "name": "Nearby attractions", "description": "input {latitude, longitude, limit}",
           "tags": ["poi", "attractions", "wikipedia"]}]
HEADERS = {"User-Agent": "a2a-travel-concierge-mesh/1.0 (educational demo)"}


def handle(data: dict) -> dict:
    lat, lon, limit = data["latitude"], data["longitude"], int(data.get("limit", 8))
    r = httpx.get("https://en.wikipedia.org/w/api.php", headers=HEADERS, timeout=20, params={
        "action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}", "gsradius": 8000,
        "gslimit": limit + 6, "format": "json"})
    r.raise_for_status()
    hits = r.json()["query"]["geosearch"]
    places = []
    for h in hits:
        s = httpx.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{h['title'].replace(' ', '_')}",
                      headers=HEADERS, timeout=20)
        if s.status_code != 200:
            continue
        j = s.json()
        extract = j.get("extract", "")
        if len(extract) < 60 or j.get("type") == "disambiguation":
            continue
        places.append({"title": j["title"], "distance_m": h["dist"], "summary": extract[:380],
                       "url": j.get("content_urls", {}).get("desktop", {}).get("page")})
        if len(places) >= limit:
            break
    return {"places": places}
