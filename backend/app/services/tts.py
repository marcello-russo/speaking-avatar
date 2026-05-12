import edge_tts
from fastapi.responses import Response

async def synthesize(text: str, voice: str = "it-IT-ElsaNeural") -> Response:
    tts = edge_tts.Communicate(text, voice)
    audio = b""
    async for chunk in tts.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
    return Response(content=audio, media_type="audio/mp3")
