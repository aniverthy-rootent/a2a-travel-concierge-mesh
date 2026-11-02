"""Currency Agent - live ECB reference rates via Frankfurter (no API key)."""
import httpx

PORT = 9103
NAME = "Currency Agent"
DESCRIPTION = "Converts amounts between currencies using the latest ECB reference rates."
SKILLS = [{"id": "convert", "name": "Convert currency", "description": "input {amount, from, to}", "tags": ["fx", "currency"]}]


def handle(data: dict) -> dict:
    amount, src, dst = float(data["amount"]), data["from"].upper(), data["to"].upper()
    if src == dst:
        return {"amount": amount, "from": src, "to": dst, "rate": 1.0, "converted": amount, "date": None}
    r = httpx.get("https://api.frankfurter.app/latest", params={"amount": amount, "from": src, "to": dst}, timeout=20)
    r.raise_for_status()
    j = r.json()
    converted = j["rates"][dst]
    return {"amount": amount, "from": src, "to": dst, "rate": round(converted / amount, 6) if amount else None,
            "converted": converted, "date": j["date"]}
