from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json, httpx, os

from app.models import ChatRequest, ChatResponse
from app.services.context import parse_context, build_prompt
from app.services.llm import chat, _fallback

router = APIRouter()

sessions: dict[str, list] = {}

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# ── Non-streaming ────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(req: ChatRequest):
    ctx = parse_context(req.context)
    session_id = req.session_id or f"session_{id(req)}"

    if session_id not in sessions:
        sessions[session_id] = []
    history = sessions[session_id]

    reply = await chat(req.message, ctx, history)
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})

    if len(history) > 50:
        history[:] = history[-50:]

    return ChatResponse(reply=reply, emotion="neutral", session_id=session_id)

# ── Streaming ────────────────────────────────────────

@router.post("/chat/stream")
async def handle_chat_stream(req: ChatRequest):
    ctx = parse_context(req.context)
    prompt = build_prompt(ctx)
    session_id = req.session_id or f"session_{id(req)}"

    if session_id not in sessions:
        sessions[session_id] = []
    history = sessions[session_id]

    async def event_stream():
        full_reply = ""
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream(
                    "POST",
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": OPENROUTER_MODEL,
                        "messages": [
                            {"role": "system", "content": prompt},
                            *history[-6:],
                            {"role": "user", "content": req.message},
                        ],
                        "stream": True,
                    },
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and line[6:] != "[DONE]":
                            try:
                                chunk = json.loads(line[6:])
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                token = delta.get("content", "")
                                if token:
                                    full_reply += token
                                    yield f"data: {json.dumps({'token': token})}\n\n"
                            except json.JSONDecodeError:
                                pass
        except Exception:
            yield f"data: {json.dumps({'token': _fallback(req.message)})}\n\n"

        # Save to history
        if full_reply:
            history.append({"role": "user", "content": req.message})
            history.append({"role": "assistant", "content": full_reply})
            if len(history) > 50:
                history[:] = history[-50:]

        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
