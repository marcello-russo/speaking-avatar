import hashlib
import json
import os
from collections import OrderedDict
from typing import Optional


L2_DIR = os.path.join(os.path.dirname(__file__), "../../data/tts-cache")


class AudioCache:
    def __init__(self, max_l1: int = 20):
        self.max_l1 = max_l1
        self._l1: OrderedDict[str, list[dict]] = OrderedDict()
        self._load_l2()

    def normalize(self, text: str) -> str:
        norm = " ".join(text.lower().split())
        return hashlib.md5(norm.encode()).hexdigest()

    def get(self, text: str) -> Optional[list[dict]]:
        key = self.normalize(text)
        if key in self._l1:
            self._l1.move_to_end(key)
            return self._l1[key]
        return None

    def put(self, text: str, chunks: list[dict]):
        key = self.normalize(text)
        self._l1[key] = chunks
        if len(self._l1) > self.max_l1:
            self._l1.popitem(last=False)

    def _load_l2(self):
        if not os.path.isdir(L2_DIR):
            return
        for fname in os.listdir(L2_DIR):
            if fname.endswith(".json"):
                path = os.path.join(L2_DIR, fname)
                try:
                    with open(path) as f:
                        data = json.load(f)
                        self._l1[data["key"]] = data["chunks"]
                except (json.JSONDecodeError, KeyError):
                    continue
