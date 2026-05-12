import os, tempfile
from fastapi import APIRouter, UploadFile, File

router = APIRouter()

STT_ENGINE = os.getenv("STT_ENGINE", "mock")


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    if STT_ENGINE == "whisper":
        return await _whisper_stt(audio)
    return await _mock_stt(audio)


async def _whisper_stt(audio: UploadFile) -> dict:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        segments, _ = model.transcribe(tmp_path, language="it")
        text = " ".join(seg.text for seg in segments)
        os.unlink(tmp_path)
        return {"text": text or ""}
    except ImportError:
        return await _mock_stt(audio)


async def _mock_stt(audio: UploadFile) -> dict:
    await audio.read()
    return {"text": "Transcript from speech recognition"}
