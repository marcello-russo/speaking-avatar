from pydantic import BaseModel
from typing import Optional, Literal

class Context(BaseModel):
    course: str = ""
    lesson: str = ""
    documents: list[dict] = []

class ChatRequest(BaseModel):
    message: str
    context: str | dict | list | None = None
    session_id: str = ""
    mode: Literal["minimal", "widget", "full"] = "widget"

class ChatResponse(BaseModel):
    reply: str
    emotion: str = "neutral"
    session_id: str = ""

class TTSRequest(BaseModel):
    text: str
    voice: str = "it-IT-ElsaNeural"
