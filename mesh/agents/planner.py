"""Planner Agent - the only agent server that uses an LLM: turns verified facts into a day-by-day itinerary."""
import json

from mesh.llm import complete

PORT = 9105
NAME = "Itinerary Planner Agent"
DESCRIPTION = "Writes a day-by-day itinerary from verified facts (weather, places, budget)."
SKILLS = [{"id": "plan_itinerary", "name": "Plan itinerary", "description": "input {request, facts}",
           "tags": ["itinerary", "planning"]}]

SYSTEM = ("You are the Itinerary Planner. Build a day-by-day itinerary using ONLY the facts provided "
          "(weather per day, nearby places, budget in both currencies). Rules: put outdoor sights on the driest days; "
          "group places by proximity (distance_m is from the city centre); give a rough daily budget that sums to "
          "at most the total budget, in the traveller's budget currency AND the local currency; include one rainy-day "
          "backup. Never invent opening hours or prices. Use Markdown.")


def handle(data: dict) -> dict:
    user = f"Traveller request:\n{json.dumps(data['request'], indent=1)}\n\nVerified facts:\n{json.dumps(data['facts'], indent=1)}"
    return {"itinerary_markdown": complete(SYSTEM, user)}
