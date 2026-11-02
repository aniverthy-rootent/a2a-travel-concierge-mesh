"""Concierge - the sixth agent: understands the request, discovers the A2A agents and orchestrates them.

    python -m mesh.launch                      # terminal 1
    python concierge.py "4 days in Lisbon in late May, budget 1500 EUR, I live in the US, love food and history"
"""
import asyncio
import json
import os
import sys
from datetime import date

from dotenv import load_dotenv

from mesh.a2a import A2AClient
from mesh.llm import complete_json

REGISTRY = {  # override with AGENT_URLS='{"geo": "http://host:9101", ...}' to use remote agents
    "geo": "http://127.0.0.1:9101", "weather": "http://127.0.0.1:9102", "currency": "http://127.0.0.1:9103",
    "guide": "http://127.0.0.1:9104", "planner": "http://127.0.0.1:9105"}

PARSE_SYSTEM = ("You extract a trip request. Today is {today}. Return JSON with keys: destination (city), days (int), "
                "start_date (ISO; pick a sensible date inside the month the user mentions, default 30 days from today), "
                "budget (number), budget_currency (ISO 4217), home_currency (ISO 4217; infer from where they live, "
                "default = budget_currency), interests (list of strings).")


async def main(request_text: str) -> None:
    urls = {**REGISTRY, **json.loads(os.environ.get("AGENT_URLS", "{}"))}
    req = complete_json(PARSE_SYSTEM.format(today=date.today().isoformat()), request_text)
    print(f"Request understood: {json.dumps(req)}\n")

    a2a = A2AClient()
    try:
        print("Discovering agents via their Agent Cards:")
        for name, url in urls.items():
            card = await a2a.card(url)
            print(f"  - {card['name']}: {', '.join(s['id'] for s in card['skills'])}")

        geo = await a2a.send(urls["geo"], {"place": req["destination"]})
        print(f"\nGeo: {geo['name']}, {geo['country']} ({geo['latitude']:.2f}, {geo['longitude']:.2f}), "
              f"currency {geo['local_currency']}")
        local = geo.get("local_currency") or req["budget_currency"]

        weather, places, fx_budget, fx_home = await asyncio.gather(
            a2a.send(urls["weather"], {"latitude": geo["latitude"], "longitude": geo["longitude"],
                                       "start_date": req["start_date"], "days": req["days"]}),
            a2a.send(urls["guide"], {"latitude": geo["latitude"], "longitude": geo["longitude"], "limit": 8}),
            a2a.send(urls["currency"], {"amount": req["budget"], "from": req["budget_currency"], "to": local}),
            a2a.send(urls["currency"], {"amount": 100, "from": req.get("home_currency", req["budget_currency"]), "to": local}))
        print(f"Weather ({weather['source']}): avg high {weather['avg_high_c']}C, {weather['rainy_days']} rainy day(s)")
        print(f"Guide: {len(places['places'])} places | FX: budget = {fx_budget['converted']} {local} "
              f"(rate date {fx_budget['date']})")

        facts = {"destination": geo, "weather": weather, "places": places["places"],
                 "budget_in_local_currency": fx_budget, "home_to_local_100": fx_home}
        plan = await a2a.send(urls["planner"], {"request": req, "facts": facts})
    finally:
        await a2a.close()
    print("\n" + "=" * 70 + "\n" + plan["itinerary_markdown"])


if __name__ == "__main__":
    load_dotenv()
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    asyncio.run(main(" ".join(sys.argv[1:])))
