# Travel Concierge Mesh

**Framework:** A2A protocol  
**Agents:** 6

Five independent A2A agent servers (each with its own Agent Card) plus a concierge that discovers and orchestrates them using REAL free APIs: Open-Meteo, Frankfurter (ECB rates), Wikipedia, REST Countries.

> **Status:** this project was written as complete, runnable code but has **not been executed end to end against live LLM APIs** yet. It needs your own API key; expect to fix small issues from provider or library version changes. Issues and PRs welcome.

## Agents

| # | Agent | Role |
|---|---|---|
| 1 | Geo Agent | place -> coordinates, country, currency |
| 2 | Weather Agent | live forecast or last year's climate |
| 3 | Currency Agent | live FX conversion |
| 4 | Guide Agent | nearby attractions from Wikipedia |
| 5 | Itinerary Planner Agent | LLM writes the plan from verified facts only |
| 6 | Concierge | A2A client: parses the request, discovers agents, orchestrates |

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env
python -m mesh.launch      # terminal 1
python concierge.py "4 days in Lisbon in late May, budget 1500 EUR, I live in the US"   # terminal 2
```

## How it works

Agents talk over JSON-RPC (message/send) with data parts; you can host any of them on another machine.

## Configuration

See `.env.example`. Models are chosen with one `LLM_SPEC` variable so you can switch provider without touching code.

## License

MIT
