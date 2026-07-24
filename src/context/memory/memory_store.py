import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentic_builder.context.memory.memory_store")

class MemoryEntry(BaseModel):
    id: Optional[int] = None
    session_id: str
    timestamp: str
    role: str
    content: str
    tags: str = ""

class EpisodicMemoryStore:
    def __init__(self, db_path: str = ".agent/memory.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        tags TEXT DEFAULT ''
                    )
                """)
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                        content,
                        tags,
                        content='memory_entries',
                        content_rowid='id'
                    )
                """)
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS memory_after_insert AFTER INSERT ON memory_entries BEGIN
                        INSERT INTO memory_fts(rowid, content, tags) VALUES (new.id, new.content, new.tags);
                    END;
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite memory database: {e}")

    def store(self, session_id: str, role: str, content: str, tags: str = "") -> bool:
        if not content.strip():
            return False
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO memory_entries (session_id, timestamp, role, content, tags) VALUES (?, ?, ?, ?, ?)",
                    (session_id, timestamp, role, content, tags)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store memory entry: {e}")
            return False

    def recall(self, query: str, top_k: int = 3) -> list[MemoryEntry]:
        if not query.strip():
            return []
        
        # Sanitize query for FTS5 syntax
        sanitized_query = "".join(c if c.isalnum() or c.isspace() else " " for c in query).strip()
        if not sanitized_query:
            return []
        
        tokens = sanitized_query.split()
        fts_query = " OR ".join(tokens)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.id, m.session_id, m.timestamp, m.role, m.content, m.tags
                    FROM memory_entries m
                    JOIN memory_fts f ON m.id = f.rowid
                    WHERE memory_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, top_k))
                rows = cursor.fetchall()
                return [
                    MemoryEntry(
                        id=row["id"],
                        session_id=row["session_id"],
                        timestamp=row["timestamp"],
                        role=row["role"],
                        content=row["content"],
                        tags=row["tags"]
                    ) for row in rows
                ]
        except Exception as e:
            logger.warning(f"FTS5 query recall failed, falling back to LIKE: {e}")
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, session_id, timestamp, role, content, tags
                        FROM memory_entries
                        WHERE content LIKE ?
                        ORDER BY id DESC
                        LIMIT ?
                    """, (f"%{sanitized_query[:20]}%", top_k))
                    rows = cursor.fetchall()
                    return [
                        MemoryEntry(
                            id=row["id"],
                            session_id=row["session_id"],
                            timestamp=row["timestamp"],
                            role=row["role"],
                            content=row["content"],
                            tags=row["tags"]
                        ) for row in rows
                    ]
            except Exception as ex:
                logger.error(f"Fallback recall failed: {ex}")
                return []
