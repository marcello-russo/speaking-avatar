from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, tts, stt

app = FastAPI(title="Speaking Avatar API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(chat.router, prefix="/api/v1")
app.include_router(tts.router, prefix="/api/v1")
app.include_router(stt.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
