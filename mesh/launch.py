"""Start the five A2A agent servers (each is its own HTTP server with its own Agent Card).

    python -m mesh.launch              # all five, on ports 9101-9105
    python -m mesh.launch geo weather  # only some

Each agent could equally run on a different machine or in a different organization - the concierge only needs URLs.
"""
import importlib
import sys
import threading
import time

import uvicorn
from dotenv import load_dotenv

from mesh.a2a import make_agent_app

AGENTS = ["geo", "weather", "currency", "guide", "planner"]


def serve(name: str, host: str = "127.0.0.1") -> uvicorn.Server:
    mod = importlib.import_module(f"mesh.agents.{name}")
    app = make_agent_app(mod.NAME, mod.DESCRIPTION, mod.SKILLS, f"http://{host}:{mod.PORT}", mod.handle)
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=mod.PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    print(f"  {mod.NAME:<26} http://{host}:{mod.PORT}/.well-known/agent-card.json")
    return server


def main() -> None:
    load_dotenv()
    names = sys.argv[1:] or AGENTS
    print("Starting A2A agents:")
    servers = [serve(n) for n in names]
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for s in servers:
            s.should_exit = True


if __name__ == "__main__":
    main()
