from fastapi import APIRouter

from app.models import ChatRequest, ChatResponse
from app.services.context import parse_context
from app.services.llm import chat

router = APIRouter()

sessions: dict[str, list] = {}


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
