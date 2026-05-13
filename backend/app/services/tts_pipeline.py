import asyncio
import base64
from app.services.audio_cache import AudioCache


class TtsPipeline:
    def __init__(self, voice: str, audio_queue: asyncio.Queue, cache: AudioCache = None):
        self.voice = voice
        self.audio_queue = audio_queue
        self.cache = cache or AudioCache()
        self._semaphore = asyncio.Semaphore(2)

    async def enqueue(self, text: str):
        asyncio.create_task(self._synthesize(text))

    async def _synthesize(self, text: str):
        async with self._semaphore:
            cached = self.cache.get(text)
            if cached:
                for chunk in cached:
                    await self.audio_queue.put(chunk)
                return

            import edge_tts
            chunks = []
            tts = edge_tts.Communicate(text, self.voice)
            async for chunk in tts.stream():
                if chunk["type"] == "audio":
                    dur = len(chunk["data"]) / 16000
                    b64 = base64.b64encode(chunk["data"]).decode()
                    event = {
                        "type": "audio",
                        "chunk": b64,
                        "dur": round(dur, 3),
                        "visemes": _calc_visemes(text, dur),
                    }
                    chunks.append(event)
                    await self.audio_queue.put(event)

            self.cache.put(text, chunks)


def _calc_visemes(text: str, duration: float) -> list[dict]:
    spoken = text.replace(" ", "")
    if not spoken or duration <= 0:
        return []
    count = len(spoken)
    time_per_char = duration / count
    return [
        {"index": i % 21, "time": round(i * time_per_char, 3)}
        for i in range(count)
    ]
