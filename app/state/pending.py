import time
import secrets
from typing import Any

_PENDING: dict[str, dict[str, Any]] = {}

TTL_SECONDS = 300


def create(action: str, chat_id: int, payload: dict) -> str:
    token = secrets.token_urlsafe(6)
    _PENDING[token] = {
        "action": action,
        "chat_id": chat_id,
        "payload": payload,
        "created_at": time.time(),
    }
    return token


def pop(token: str, chat_id: int, action: str) -> dict | None:
    item = _PENDING.get(token)
    if not item:
        return None

    if item["chat_id"] != chat_id or item["action"] != action:
        return None

    if time.time() - item["created_at"] > TTL_SECONDS:
        _PENDING.pop(token, None)
        return None

    _PENDING.pop(token, None)
    return item["payload"]
