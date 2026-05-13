import time
from typing import Optional


class SentenceBuffer:
    def __init__(self, soglia_base: int = 80, timeout_ms: int = 800):
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

        # Merge apostrophe tokens with previous word
        if token.startswith("'") and self._tokens:
            self._tokens[-1] += token
            return None

        if self._ready_to_emit:
            result = self._emit_all_but_last()
            self._tokens.append(token)
            self._first_token_time = time.monotonic()
            self._ready_to_emit = False
            return result

        self._tokens.append(token)
        if self._first_token_time is None:
            self._first_token_time = time.monotonic()
        return self._check_and_emit()

    def _check_and_emit(self) -> Optional[str]:
        full = " ".join(self._tokens)
        last = self._tokens[-1] if self._tokens else ""

        # Standalone punctuation → emit whole sentence
        if last in (".", "!", "?"):
            return self._emit()

        # Embedded punctuation in the accumulated text (not in last token)
        if any(c in full[:-(len(last) + 1)] if len(last) < len(full) else False for c in ".!?"):
            self._ready_to_emit = True
            return None

        # Forced emit at word boundary (threshold + backpressure)
        threshold = self.soglia_base + (self._queue_depth * 30)
        if len(full) >= threshold:
            return self._emit_at_word_boundary()

        # Timeout-based emit at word boundary
        if self._first_token_time is not None:
            elapsed = (time.monotonic() - self._first_token_time) * 1000
            if elapsed >= self.timeout_ms:
                return self._emit_at_word_boundary()

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

    def _emit_all_but_last(self) -> str:
        result = " ".join(self._tokens[:-1])
        last = self._tokens[-1]
        self._tokens = [last]
        self._first_token_time = None
        self._ready_to_emit = False
        return result

    def _emit_at_word_boundary(self) -> str:
        full = " ".join(self._tokens)
        space = full.rfind(" ")
        if space <= 0:
            return self._emit()
        result = full[:space]
        remainder = full[space + 1:]
        self._tokens = remainder.split(" ") if remainder else []
        self._first_token_time = time.monotonic()
        self._ready_to_emit = False
        return result
