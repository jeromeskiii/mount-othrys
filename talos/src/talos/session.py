from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


SESSION_DIR = Path.home() / ".sisyphus" / "talos-sessions"


@dataclass
class TalosSession:
    session_id: str
    created_at: str
    updated_at: str
    messages: list[dict] = field(default_factory=list)
    todos: list[dict] = field(default_factory=list)
    titan: str = ""
    objective: str = ""
    status: str = "active"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


def create_session(titan: str = "", objective: str = "") -> TalosSession:
    _ensure_dir()
    existing = sorted(SESSION_DIR.glob("session_*.json"))
    n = 1
    if existing:
        last = existing[-1].stem
        try:
            n = int(last.split("_")[1]) + 1
        except (IndexError, ValueError):
            n = 1
    sid = f"session_{n:04d}"
    session = TalosSession(
        session_id=sid,
        created_at=_now(),
        updated_at=_now(),
        titan=titan,
        objective=objective,
    )
    _save(session)
    return session


def load_session(session_id: str) -> TalosSession | None:
    _ensure_dir()
    path = SESSION_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return TalosSession(**data)


def save_session(session: TalosSession) -> None:
    session.updated_at = _now()
    _save(session)


def _save(session: TalosSession) -> None:
    _ensure_dir()
    path = SESSION_DIR / f"{session.session_id}.json"
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(session.__dict__, indent=2, default=str))
    tmp.replace(path)


def append_message(session: TalosSession, role: str, content: str) -> TalosSession:
    session.messages.append({"role": role, "content": content, "ts": _now()})
    save_session(session)
    return session


def update_todos(session: TalosSession, todos: list[dict]) -> TalosSession:
    session.todos = todos
    save_session(session)
    return session


def list_sessions() -> list[TalosSession]:
    _ensure_dir()
    out: list[TalosSession] = []
    for p in sorted(SESSION_DIR.glob("session_*.json")):
        try:
            data = json.loads(p.read_text())
            out.append(TalosSession(**data))
        except Exception:
            continue
    return out


def delete_session(session_id: str) -> None:
    path = SESSION_DIR / f"{session_id}.json"
    if path.exists():
        path.unlink()