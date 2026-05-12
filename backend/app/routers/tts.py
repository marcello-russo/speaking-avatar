from fastapi import APIRouter, HTTPException
from app.models import TTSRequest
from app.services.tts import synthesize

router = APIRouter()

@router.post("/tts")
async def handle_tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    return await synthesize(req.text, req.voice)
