import sqlite3
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from attune.models.email import Email

CACHE_DIR = Path.home() / ".attune"
CACHE_DB = CACHE_DIR / "email_cache.db"

_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        CACHE_DIR.mkdir(exist_ok=True)
        _conn = sqlite3.connect(CACHE_DB)
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS email_embeddings (
                email_id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_preview TEXT,
                embedding BLOB NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        _conn.commit()
    return _conn


def init_cache() -> None:
    _get_conn()


def cache_email(email: Email, embedding: np.ndarray) -> None:
    conn = _get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO email_embeddings
        (email_id, sender, subject, body_preview, embedding, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        email.id,
        email.sender,
        email.subject,
        email.body[:500] if email.body else "",
        embedding.tobytes(),
        email.timestamp,
    ))
    conn.commit()


def is_cached(email_id: str) -> bool:
    conn = _get_conn()
    row = conn.execute(
        "SELECT 1 FROM email_embeddings WHERE email_id = ?", (email_id,)
    ).fetchone()
    return row is not None


def get_cached_embedding(email_id: str) -> Optional[np.ndarray]:
    conn = _get_conn()
    row = conn.execute(
        "SELECT embedding FROM email_embeddings WHERE email_id = ?", (email_id,)
    ).fetchone()
    if row is None:
        return None
    return np.frombuffer(row[0], dtype=np.float32)


def get_cached_emails(since_ts: Optional[str] = None) -> List[Tuple[Email, np.ndarray]]:
    conn = _get_conn()
    if since_ts is None:
        rows = conn.execute(
            "SELECT email_id, sender, subject, body_preview, embedding, timestamp FROM email_embeddings"
        ).fetchall()
    else:
        # ISO 8601 timestamps compare correctly as strings
        rows = conn.execute(
            "SELECT email_id, sender, subject, body_preview, embedding, timestamp "
            "FROM email_embeddings WHERE timestamp >= ?",
            (since_ts,)
        ).fetchall()

    result = []
    for email_id, sender, subject, body_preview, embedding_bytes, timestamp in rows:
        email = Email(
            id=email_id,
            sender=sender,
            subject=subject,
            body=body_preview,
            timestamp=timestamp,
        )
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        result.append((email, embedding))

    return result


def clear_cache() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    if CACHE_DB.exists():
        CACHE_DB.unlink()
