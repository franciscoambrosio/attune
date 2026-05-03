import sqlite3
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from attune.models.email import Email

CACHE_DIR = Path.home() / ".attune"
CACHE_DB = CACHE_DIR / "email_cache.db"


def init_cache() -> None:
    """Initialize SQLite cache database for email embeddings."""
    CACHE_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_embeddings (
            email_id TEXT PRIMARY KEY,
            sender TEXT NOT NULL,
            subject TEXT NOT NULL,
            body_preview TEXT,
            embedding BLOB NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def cache_email(email: Email, embedding: np.ndarray) -> None:
    """Store email with its embedding in cache."""
    init_cache()

    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO email_embeddings
        (email_id, sender, subject, body_preview, embedding, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        email.id,
        email.sender,
        email.subject,
        email.body[:500] if email.body else "",
        embedding.tobytes(),
        email.timestamp
    ))
    conn.commit()
    conn.close()


def is_cached(email_id: str) -> bool:
    """Check if email is already cached."""
    if not CACHE_DB.exists():
        return False

    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM email_embeddings WHERE email_id = ?", (email_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_cached_emails(since_ts: Optional[float] = None) -> List[Tuple[Email, np.ndarray]]:
    """Retrieve cached emails with their embeddings."""
    if not CACHE_DB.exists():
        return []

    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()

    if since_ts is None:
        cursor.execute("SELECT email_id, sender, subject, body_preview, embedding, timestamp FROM email_embeddings")
    else:
        cursor.execute(
            "SELECT email_id, sender, subject, body_preview, embedding, timestamp FROM email_embeddings WHERE timestamp >= ?",
            (since_ts,)
        )

    rows = cursor.fetchall()
    conn.close()

    result = []
    for email_id, sender, subject, body_preview, embedding_bytes, timestamp in rows:
        email = Email(
            id=email_id,
            sender=sender,
            subject=subject,
            body=body_preview,
            timestamp=timestamp
        )
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        result.append((email, embedding))

    return result


def clear_cache() -> None:
    """Clear the entire cache (for testing/reset)."""
    if CACHE_DB.exists():
        CACHE_DB.unlink()
