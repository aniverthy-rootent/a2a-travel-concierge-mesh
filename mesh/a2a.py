"""Minimal, spec-shaped A2A (Agent2Agent) server + client.

Server : GET /.well-known/agent-card.json  and  POST / (JSON-RPC 2.0: message/send, tasks/get)
Client : fetch agent cards (discovery) and send structured (data-part) or text messages.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any, Callable

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

PROTOCOL_VERSION = "0.3.0"


def make_agent_app(name: str, description: str, skills: list[dict], base_url: str,
                   handler: Callable[[dict], dict]) -> Starlette:
    """handler receives the first data part of the incoming message and returns a dict (the result)."""
    card = {"protocolVersion": PROTOCOL_VERSION, "name": name, "description": description, "url": base_url,
            "version": "1.0.0", "capabilities": {"streaming": False, "pushNotifications": False},
            "defaultInputModes": ["application/json", "text/plain"],
            "defaultOutputModes": ["application/json", "text/plain"], "skills": skills}
    tasks: dict[str, dict] = {}

    async def agent_card(_: Request) -> JSONResponse:
        return JSONResponse(card)

    async def rpc(request: Request) -> JSONResponse:
        body = await request.json()
        rid, method, params = body.get("id"), body.get("method"), body.get("params", {})
        if method == "message/send":
            parts = params["message"]["parts"]
            data = next((p["data"] for p in parts if p.get("kind") == "data"), None)
            if data is None:
                text = "".join(p.get("text", "") for p in parts if p.get("kind") == "text")
                data = {"text": text}
            task_id = str(uuid.uuid4())
            try:
                result = await asyncio.to_thread(handler, data)
                state, art_parts = "completed", [{"kind": "data", "data": result},
                                                 {"kind": "text", "text": json.dumps(result)[:2000]}]
            except Exception as exc:  # report failures as A2A task failures, never crash the server
                state, art_parts = "failed", [{"kind": "text", "text": f"{type(exc).__name__}: {exc}"}]
            task = {"kind": "task", "id": task_id, "contextId": params["message"].get("contextId", task_id),
                    "status": {"state": state}, "artifacts": [{"artifactId": str(uuid.uuid4()), "name": "result",
                                                               "parts": art_parts}]}
            tasks[task_id] = task
            return JSONResponse({"jsonrpc": "2.0", "id": rid, "result": task})
        if method == "tasks/get":
            task = tasks.get(params.get("id"))
            if task:
                return JSONResponse({"jsonrpc": "2.0", "id": rid, "result": task})
            return JSONResponse({"jsonrpc": "2.0", "id": rid, "error": {"code": -32001, "message": "Task not found"}})
        return JSONResponse({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}})

    return Starlette(routes=[Route("/.well-known/agent-card.json", agent_card),
                             Route("/", rpc, methods=["POST"])])


class A2AClient:
    def __init__(self, timeout: float = 120) -> None:
        self.http = httpx.AsyncClient(timeout=timeout)

    async def card(self, base_url: str) -> dict[str, Any]:
        r = await self.http.get(base_url.rstrip("/") + "/.well-known/agent-card.json")
        r.raise_for_status()
        return r.json()

    async def send(self, base_url: str, data: dict) -> dict:
        payload = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "message/send",
                   "params": {"message": {"kind": "message", "role": "user", "messageId": str(uuid.uuid4()),
                                          "parts": [{"kind": "data", "data": data}]}}}
        r = await self.http.post(base_url.rstrip("/") + "/", json=payload)
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            raise RuntimeError(body["error"]["message"])
        task = body["result"]
        parts = task["artifacts"][0]["parts"]
        if task["status"]["state"] != "completed":
            raise RuntimeError(parts[0].get("text", "agent failed"))
        return next(p["data"] for p in parts if p.get("kind") == "data")

    async def close(self) -> None:
        await self.http.aclose()
