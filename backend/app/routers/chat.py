from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json, httpx, asyncio

from app.models import ChatRequest, ChatResponse
from app.services.context import parse_context, build_prompt
from app.services.llm import chat, _fallback, LLM_PROVIDER, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL
from app.services.sentence_buffer import SentenceBuffer
from app.services.tts_pipeline import TtsPipeline

router = APIRouter()

sessions: dict[str, list] = {}

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

def _get_stream_config():
    """Return (url, headers, model, is_anthropic) for the current LLM_PROVIDER."""
    if LLM_PROVIDER == "openai":
        return (
            f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
            {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            OPENAI_MODEL,
            False,
        )
    elif LLM_PROVIDER == "openrouter":
        return (
            "https://openrouter.ai/api/v1/chat/completions",
            {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            OPENROUTER_MODEL,
            False,
        )
    elif LLM_PROVIDER == "anthropic":
        return (
            f"{ANTHROPIC_BASE_URL.rstrip('/')}/v1/messages",
            {"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            ANTHROPIC_MODEL,
            True,
        )
    return (None, None, None, False)


async def _merge_iterators(*iters):
    queue: asyncio.Queue = asyncio.Queue()
    finished = 0
    n = len(iters)

    async def feed(it):
        nonlocal finished
        try:
            async for item in it:
                await queue.put(item)
        finally:
            finished += 1
            if finished == n:
                await queue.put(None)

    tasks = [asyncio.create_task(feed(it)) for it in iters]
    while True:
        item = await queue.get()
        if item is None:
            break
        yield item


async def _token_stream(prompt, history, message, ctx):
    url, headers, model, is_anthropic = _get_stream_config()
    has_key = any(v for v in headers.values() if v.startswith("Bearer ") or len(v) > 10)
    full_reply = ""

    if url and has_key:
        try:
            if is_anthropic:
                body = {
                    "model": model,
                    "system": prompt,
                    "messages": [
                        *history[-6:],
                        {"role": "user", "content": message},
                    ],
                    "stream": True,
                    "max_tokens": 4096,
                }
            else:
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": prompt},
                        *history[-6:],
                        {"role": "user", "content": message},
                    ],
                    "stream": True,
                }

            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", url, headers=headers, json=body) as resp:
                    if is_anthropic:
                        pending_event = ""
                        async for line in resp.aiter_lines():
                            if line.startswith("event: "):
                                pending_event = line[7:]
                            elif line.startswith("data: ") and pending_event == "content_block_delta":
                                try:
                                    chunk = json.loads(line[6:])
                                    dd = chunk.get("delta", {})
                                    if dd.get("type") == "text_delta":
                                        token = dd.get("text", "")
                                        if token:
                                            full_reply += token
                                            yield {"type": "token", "text": token}
                                except json.JSONDecodeError:
                                    pass
                    else:
                        async for line in resp.aiter_lines():
                            if line.startswith("data: ") and line[6:] != "[DONE]":
                                try:
                                    chunk = json.loads(line[6:])
                                    token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if token:
                                        full_reply += token
                                        yield {"type": "token", "text": token}
                                except json.JSONDecodeError:
                                    pass
        except Exception:
            pass

    if not full_reply:
        reply = await chat(message, ctx, history)
        yield {"type": "token", "text": reply}


@router.post("/chat/stream")
async def handle_chat_stream(req: ChatRequest):
    ctx = parse_context(req.context)
    prompt = build_prompt(ctx)
    session_id = req.session_id or f"session_{id(req)}"

    if session_id not in sessions:
        sessions[session_id] = []
    history = sessions[session_id]

    async def event_stream():
        sentence_buffer = SentenceBuffer(timeout_ms=800)
        audio_queue: asyncio.Queue = asyncio.Queue()
        tts_pipeline = TtsPipeline(req.voice, audio_queue)

        async def audio_drainer():
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                yield chunk

        full_reply = ""
        merged = _merge_iterators(
            _token_stream(prompt, history, req.message, ctx),
            audio_drainer(),
        )

        async for event in merged:
            if event["type"] == "token":
                full_reply += event["text"]
                frase = sentence_buffer.push(event["text"])
                if frase:
                    asyncio.create_task(tts_pipeline.enqueue(frase))
                yield f"data: {json.dumps({'token': event['text']})}\n\n"
            elif event["type"] == "audio" or event["type"] == "audio_complete":
                yield f"data: {json.dumps(event)}\n\n"

        remainder = sentence_buffer.flush()
        if remainder:
            asyncio.create_task(tts_pipeline.enqueue(remainder))

        if full_reply:
            history.append({"role": "user", "content": req.message})
            history.append({"role": "assistant", "content": full_reply})
            if len(history) > 50:
                history[:] = history[-50:]

        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
