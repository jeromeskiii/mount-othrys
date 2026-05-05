from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Handshake:
    source_titan: str
    target_titan: str
    payload: dict[str, Any]
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)


class FortressStore:
    """The 'Unified Blackboard' for Mount Othrys.

    Persists cross-titan context, campaign state, and semantic findings.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # Campaigns: High-level missions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    lead_titan TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            # Handshakes: Structured data transfer between Titans
            cur.execute("""
                CREATE TABLE IF NOT EXISTS handshakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT REFERENCES campaigns(id),
                    source_titan TEXT NOT NULL,
                    target_titan TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    created_at REAL NOT NULL
                )
            """)
            # Knowledge: Shared findings and architectural decisions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT REFERENCES campaigns(id),
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    titan TEXT NOT NULL,
                    metadata TEXT,
                    created_at REAL NOT NULL
                )
            """)
            conn.commit()

    def create_campaign(self, objective: str, lead_titan: str = "kronos") -> str:
        import uuid
        cid = str(uuid.uuid4())
        now = time.time()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO campaigns VALUES (?, ?, ?, ?, ?, ?)",
                (cid, objective, "active", lead_titan, now, now)
            )
            conn.commit()
        return cid

    def record_handshake(self, campaign_id: str, handshake: Handshake) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO handshakes (campaign_id, source_titan, target_titan, payload, confidence, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (campaign_id, handshake.source_titan, handshake.target_titan,
                 json.dumps(handshake.payload), handshake.confidence, handshake.timestamp)
            )
            conn.commit()

    def store_finding(self, campaign_id: str, key: str, value: str, titan: str, metadata: dict | None = None) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO knowledge (campaign_id, key, value, titan, metadata, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (campaign_id, key, value, titan, json.dumps(metadata or {}), time.time())
            )
            conn.commit()

    def get_campaign_context(self, campaign_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            # Verify campaign exists
            cur = conn.execute("SELECT 1 FROM campaigns WHERE id = ?", (campaign_id,))
            if not cur.fetchone():
                raise KeyError(f"Campaign not found: {campaign_id}")

            conn.row_factory = sqlite3.Row
            # Get findings
            cur = conn.execute("SELECT key, value, titan FROM knowledge WHERE campaign_id = ?", (campaign_id,))
            findings = [dict(r) for r in cur.fetchall()]

            # Get latest handshake
            cur = conn.execute(
                "SELECT source_titan, payload FROM handshakes WHERE campaign_id = ? ORDER BY created_at DESC LIMIT 1",
                (campaign_id,)
            )
            row = cur.fetchone()
            latest_payload = json.loads(row["payload"]) if row else {}

            return {
                "findings": findings,
                "latest_context": latest_payload
            }
