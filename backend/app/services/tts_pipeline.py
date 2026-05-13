import asyncio
import base64
from app.services.audio_cache import AudioCache


class TtsPipeline:
    def __init__(self, voice: str, audio_queue: asyncio.Queue, cache: AudioCache = None):
        self.voice = voice
        self.audio_queue = audio_queue
        self.cache = cache or AudioCache()
        self._semaphore = asyncio.Semaphore(5)  # I/O-bound, più concorrenza = meglio
        self._pending = 0
        self._all_done = asyncio.Event()
        self._all_done.set()

    async def enqueue(self, text: str):
        self._pending += 1
        self._all_done.clear()

    async def enqueue(self, text: str):
        self._pending += 1
        asyncio.create_task(self._synthesize(text))

    async def _synthesize(self, text: str):
        try:
            async with self._semaphore:
                cached = self.cache.get(text)
                if cached:
                    await self.audio_queue.put(cached)
                    return

                import edge_tts
                audio_bytes = bytearray()
                total_dur = 0.0
                tts = edge_tts.Communicate(text, self.voice)
                async for chunk in tts.stream():
                    if chunk["type"] == "audio":
                        audio_bytes.extend(chunk["data"])
                        total_dur += len(chunk["data"]) / 16000

                if not audio_bytes:
                    return

                full_mp3 = bytes(audio_bytes)
                event = {
                    "type": "audio_complete",
                    "data": base64.b64encode(full_mp3).decode(),
                    "dur": round(total_dur, 3),
                    "visemes": _calc_visemes(text, total_dur),
                }
                self.cache.put(text, event)
                await self.audio_queue.put(event)
        except Exception:
            pass
        finally:
            self._pending -= 1
            if self._pending == 0:
                self._all_done.set()
                await self.audio_queue.put(None)

    async def wait_for_all(self, timeout: float = 30.0):
        try:
            await asyncio.wait_for(self._all_done.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            import sys
            print(f"[TtsPipeline] timeout after {timeout}s, {self._pending} tasks still pending", file=sys.stderr)


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
