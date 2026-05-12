import os, httpx
from .context import build_prompt

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

async def chat(message: str, ctx: dict, history: list | None = None) -> str:
    prompt = build_prompt(ctx)
    if LLM_PROVIDER == "ollama":
        return await _ollama(message, prompt)
    return await _openrouter(message, prompt, history)


async def _openrouter(message: str, prompt: str, history: list | None = None) -> str:
    if not OPENROUTER_API_KEY:
        return _fallback(message)
    messages = [{"role": "system", "content": prompt}]
    if history:
        messages.extend(history[-6:])  # keep last 6 turns
    messages.append({"role": "user", "content": message})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
                json={"model": OPENROUTER_MODEL, "messages": messages},
            )
            data = resp.json()
            if "error" in data:
                return _fallback(message)
            return data["choices"][0]["message"]["content"]
    except Exception:
        return _fallback(message)


async def _ollama(message: str, prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message},
                ], "stream": False},
            )
            data = resp.json()
            return data.get("message", {}).get("content", "")
    except Exception:
        return _fallback(message)


def _fallback(msg: str) -> str:
    m = msg.lower()
    if "hello" in m or "hi" in m or "ciao" in m:
        return "Hello! I'm your AI tutor. How can I help you today?"
    return f"Interesting! Tell me more about '{msg[:60]}' so I can help."
