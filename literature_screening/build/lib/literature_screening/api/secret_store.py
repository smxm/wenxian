from __future__ import annotations

import threading
import uuid


class SecretStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, str] = {}

    def put(self, secret: str) -> str:
        secret_id = uuid.uuid4().hex[:16]
        with self._lock:
            self._items[secret_id] = secret
        return secret_id

    def get(self, secret_id: str | None) -> str | None:
        if not secret_id:
            return None
        with self._lock:
            return self._items.get(secret_id)

