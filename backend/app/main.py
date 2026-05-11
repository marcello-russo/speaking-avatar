from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import httpx, os, edge_tts
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Speaking Avatar API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT",
    "You are a friendly AI tutor. Answer clearly and engagingly. "
    "Always reply in the user's language. Context: {context}")

class ChatRequest(BaseModel):
    message: str
    context: str = ""

class ChatResponse(BaseModel):
    reply: str
    emotion: str = "neutral"

class TTSRequest(BaseModel):
    text: str
    voice: str = "it-IT-ElsaNeural"

# ── API v1 routes ──────────────────────────────────────

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not OPENROUTER_API_KEY:
        return fallback(req.message)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": OPENROUTER_MODEL,
                      "messages": [
                          {"role": "system", "content": SYSTEM_PROMPT.format(context=req.context)},
                          {"role": "user", "content": req.message}]})
            data = resp.json()
            if "error" in data: return fallback(req.message)
            reply = data["choices"][0]["message"]["content"]
            return ChatResponse(reply=reply)
    except: return fallback(req.message)

@app.post("/api/v1/tts")
async def text_to_speech(req: TTSRequest):
    try:
        tts = edge_tts.Communicate(req.text, req.voice)
        audio = b""
        async for chunk in tts.stream():
            if chunk["type"] == "audio": audio += chunk["data"]
        return Response(content=audio, media_type="audio/mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Helpers ────────────────────────────────────────────

def fallback(msg: str) -> ChatResponse:
    m = msg.lower()
    if "hello" in m or "hi" in m: return ChatResponse(reply="Hello! I'm your AI tutor. How can I help you today?", emotion="happy")
    return ChatResponse(reply=f"Tell me more about '{msg[:60]}' so I can help!", emotion="neutral")
