from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


SESSION_DIR = Path(r"C:\Users\nutty\Documents\workspace\AI\ironclaw_tool\test\sessions")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(payload: dict[str, Any]) -> str:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid4().hex
    session = {
        "token": token,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        **payload,
    }
    (SESSION_DIR / f"{token}.json").write_text(json.dumps(session, indent=2), encoding="utf-8")
    return token


def load_session(token: str) -> dict[str, Any] | None:
    path = SESSION_DIR / f"{token}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def update_session(token: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    session = load_session(token)
    if session is None:
        return None
    session.update(patch)
    session["updated_at"] = _now_iso()
    (SESSION_DIR / f"{token}.json").write_text(json.dumps(session, indent=2), encoding="utf-8")
    return session

