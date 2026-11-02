"""Provider-agnostic LLM client over plain HTTPS (stdlib). LLM_SPEC="<provider>:<model>"."""
from __future__ import annotations

import json
import os
import urllib.request

PROVIDERS = {  # provider -> (url, api-key env var, request style)
    "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY", "openai"),
    "anthropic": ("https://api.anthropic.com/v1/messages", "ANTHROPIC_API_KEY", "anthropic"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", "GEMINI_API_KEY", "gemini"),
    "mistral": ("https://api.mistral.ai/v1/chat/completions", "MISTRAL_API_KEY", "openai"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "openai"),
    "deepseek": ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY", "openai"),
    "xai": ("https://api.x.ai/v1/chat/completions", "XAI_API_KEY", "openai"),
    "together": ("https://api.together.xyz/v1/chat/completions", "TOGETHER_API_KEY", "openai"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "openai"),
    "ollama": ("http://localhost:11434/api/chat", None, "ollama"),
}


def _post(url: str, headers: dict, payload: dict) -> dict:
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def complete(system: str, user: str) -> str:
    spec = os.environ.get("LLM_SPEC", "openai:gpt-4o-mini")
    provider, _, model = spec.partition(":")
    if provider not in PROVIDERS:
        raise ValueError(f"unsupported LLM_SPEC provider: {provider}")
    url, env, style = PROVIDERS[provider]
    key = os.environ.get(env, "") if env else ""
    if env and not key:
        raise RuntimeError(f"{env} is not set")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if style == "anthropic":
        d = _post(url, {"x-api-key": key, "anthropic-version": "2023-06-01"},
                  {"model": model, "max_tokens": 2000, "system": system, "messages": [{"role": "user", "content": user}]})
        return "".join(b.get("text", "") for b in d["content"])
    if style == "gemini":
        d = _post(url.format(model=model) + f"?key={key}", {},
                  {"system_instruction": {"parts": [{"text": system}]},
                   "contents": [{"role": "user", "parts": [{"text": user}]}]})
        return d["candidates"][0]["content"]["parts"][0]["text"]
    if style == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return _post(host + "/api/chat", {}, {"model": model, "stream": False, "messages": msgs})["message"]["content"]
    d = _post(url, {"Authorization": f"Bearer {key}"}, {"model": model, "messages": msgs})
    return d["choices"][0]["message"]["content"]


def complete_json(system: str, user: str) -> dict:
    """Ask for JSON and parse the first {...} block in the reply."""
    import re

    text = complete(system + "\nReply with ONLY a JSON object, no prose.", user)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"model did not return JSON: {text[:200]}")
    return json.loads(m.group(0))
