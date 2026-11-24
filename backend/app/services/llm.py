import os, httpx
from .context import build_prompt

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

async def chat(message: str, ctx: dict, history: list | None = None) -> str:
    prompt = build_prompt(ctx)
    if LLM_PROVIDER == "ollama":
        return await _ollama(message, prompt, ctx)
    elif LLM_PROVIDER == "anthropic":
        return await _anthropic(message, prompt, history, ctx)
    elif LLM_PROVIDER == "openai":
        return await _openai_compat(message, prompt, history, ctx)
    else:
        return await _openrouter(message, prompt, history, ctx)


async def _openrouter(message: str, prompt: str, history: list | None = None, ctx: dict | None = None) -> str:
    if not OPENROUTER_API_KEY:
        return _fallback(message, ctx)
    messages = [{"role": "system", "content": prompt}]
    if history:
        messages.extend(history[-6:])
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
                return _fallback(message, ctx)
            return data["choices"][0]["message"]["content"]
    except Exception:
        return _fallback(message, ctx)
async def _ollama(message: str, prompt: str, ctx: dict | None = None) -> str:
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
        return _fallback(message, ctx)


async def _openai_compat(message: str, prompt: str, history: list | None = None, ctx: dict | None = None) -> str:
    if not OPENAI_API_KEY:
        return _fallback(message, ctx)
    messages = [{"role": "system", "content": prompt}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": message})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": OPENAI_MODEL, "messages": messages},
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        return _fallback(message, ctx)


async def _anthropic(message: str, prompt: str, history: list | None = None, ctx: dict | None = None) -> str:
    if not ANTHROPIC_API_KEY:
        return _fallback(message, ctx)
    system = prompt
    messages_list = []
    if history:
        messages_list.extend(history[-6:])
    messages_list.append({"role": "user", "content": message})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{ANTHROPIC_BASE_URL.rstrip('/')}/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                json={"model": ANTHROPIC_MODEL, "system": system, "messages": messages_list, "max_tokens": 4096},
            )
            data = resp.json()
            if "error" in data:
                return _fallback(message, ctx)
            return data["content"][0]["text"]
    except Exception:
        return _fallback(message, ctx)


def _fallback(msg: str, ctx: dict | None = None) -> str:
    m = msg.lower()
    course = ctx.get("course", "") if ctx else ""
    lesson = ctx.get("lesson", "") if ctx else ""
    ctx_str = f" su {course}" if course else ""
    ctx_lesson = f" - {lesson}" if lesson else ""

    if "ciao" in m or "buongiorno" in m or "salve" in m or "hello" in m or "hi" in m:
        return f"Ciao! Benvenuto{ctx_str}{ctx_lesson}. Come posso aiutarti oggi?"
    if "spiegami" in m or "cosa" in m or "questa" in m or "explain" in m or "what" in m:
        return f"Buona domanda! Sto ancora configurando il mio accesso all'AI per darti risposte precise su '{course or 'questo argomento'}{ctx_lesson}'. Riprova più tardi o chiedimi qualcosa di più specifico."
    if "grazie" in m or "thanks" in m:
        return "Di niente! Sono qui per aiutarti."
    return f"Interessante! Raccontami di più così posso aiutarti meglio."
