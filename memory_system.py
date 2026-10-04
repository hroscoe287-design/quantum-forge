from __future__ import annotations
import json, math, os, sqlite3, threading, time, uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
DB_PATH = Path(os.getenv("FORGE_MEMORY_DB", str(ROOT / "data" / "memory.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_LOCK = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
 id TEXT PRIMARY KEY,
 created_at REAL NOT NULL,
 kind TEXT NOT NULL,
 project_id TEXT,
 topic TEXT,
 content TEXT NOT NULL,
 confidence REAL DEFAULT 0.5,
 source TEXT DEFAULT 'agent',
 times_used INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);
"""

def _conn():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    c.executescript(SCHEMA)
    return c

def _tokens(text: str) -> set[str]:
    return {x.lower() for x in __import__("re").findall(r"[A-Za-z0-9_]{3,}", text) if x.lower() not in {
        "the","and","for","with","that","this","from","into","about","what","using","research","project"
    }}

def _score(query: str, text: str, confidence: float) -> float:
    a, b = _tokens(query), _tokens(text)
    if not a or not b:
        return 0.0
    overlap = len(a & b) / math.sqrt(len(a) * len(b))
    return overlap * (0.7 + 0.3 * max(0.0, min(1.0, confidence)))

def remember(content: str, kind: str = "lesson", project_id: str | None = None,
             topic: str = "", confidence: float = 0.5, source: str = "agent") -> str:
    mid = str(uuid.uuid4())
    with _LOCK, _conn() as c:
        c.execute("INSERT INTO memories VALUES (?,?,?,?,?,?,?,?,?)",
                  (mid, time.time(), kind, project_id, topic, content,
                   float(confidence), source, 0))
    return mid

def recall(query: str, limit: int = 12, project_id: str | None = None) -> list[dict[str, Any]]:
    with _LOCK, _conn() as c:
        if project_id:
            rows = c.execute("SELECT * FROM memories WHERE project_id=? OR project_id IS NULL ORDER BY created_at DESC LIMIT 500", (project_id,)).fetchall()
        else:
            rows = c.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT 500").fetchall()
        ranked = sorted(rows, key=lambda r: (_score(query, r["content"] + " " + r["topic"], r["confidence"]),
                                             r["created_at"] / 1e12), reverse=True)
        chosen = ranked[:limit]
        for r in chosen:
            c.execute("UPDATE memories SET times_used=times_used+1 WHERE id=?", (r["id"],))
        return [dict(r) for r in chosen]

def learn_from_cycle(project_id: str, objective: str, report: str,
                     findings: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[str]:
    ids = []
    ids.append(remember(
        report[:5000], kind="cycle_report", project_id=project_id,
        topic=objective[:500], confidence=0.6, source="synthesis"
    ))
    for f in findings:
        text = f.get("text", "")
        if text:
            ids.append(remember(text[:3500], kind="agent_finding", project_id=project_id,
                                topic=objective[:300], confidence=0.5, source=f.get("agent","agent")))
    if evidence:
        digest = "\n".join(
            f"{x.get('title','')}: {x.get('summary','')[:700]}" for x in evidence[:8]
        )
        if digest:
            ids.append(remember(digest, kind="evidence_digest", project_id=project_id,
                                topic=objective[:300], confidence=0.7, source="arXiv"))
    return ids

def stats() -> dict[str, Any]:
    with _LOCK, _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_kind = {r[0]: r[1] for r in c.execute("SELECT kind,COUNT(*) FROM memories GROUP BY kind")}
        return {"database": str(DB_PATH), "memories": total, "by_kind": by_kind}
