import time
from typing import Optional


class SentenceBuffer:
    def __init__(self, soglia_base: int = 80, timeout_ms: int = 3000):
        self.soglia_base = soglia_base
        self.timeout_ms = timeout_ms
        self._tokens: list[str] = []
        self._queue_depth = 0
        self._first_token_time: Optional[float] = None
        self._ready_to_emit = False

    def set_queue_depth(self, depth: int):
        self._queue_depth = depth

    def push(self, token: str) -> Optional[str]:
        if not token:
            return None
        if self._ready_to_emit:
            result = self._emit()
            self._tokens.append(token)
            self._first_token_time = time.monotonic()
            return result
        self._tokens.append(token)
        if self._first_token_time is None:
            self._first_token_time = time.monotonic()
        return self._check_and_emit()

    def _check_and_emit(self) -> Optional[str]:
        full = " ".join(self._tokens)
        threshold = self.soglia_base + (self._queue_depth * 30)

        last_token = self._tokens[-1] if self._tokens else ""
        if last_token in (".", "!", "?"):
            return self._emit()

        if any(c in full for c in ".!?"):
            self._ready_to_emit = True
            return None

        if len(full) + (1 if self._tokens else 0) >= threshold:
            return self._emit()

        if self._first_token_time is not None:
            elapsed = (time.monotonic() - self._first_token_time) * 1000
            if elapsed >= self.timeout_ms:
                return self._emit()

        return None

    def flush(self) -> str:
        if not self._tokens:
            return ""
        return self._emit()

    def queue_depth(self) -> int:
        return self._queue_depth

    def _emit(self) -> str:
        result = " ".join(self._tokens)
        self._tokens.clear()
        self._first_token_time = None
        self._ready_to_emit = False
        return result
