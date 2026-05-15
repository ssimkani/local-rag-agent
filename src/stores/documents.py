import sqlite3
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict  # doc_type, title, date, author, etc.


class DocumentStore:
    def __init__(self, sqlite_path: Path, files_dir: Path):
        self.sqlite_path = sqlite_path
        self.files_dir = files_dir
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def put(self, chunk: Chunk) -> None:
        file_path = self.files_dir / f"{chunk.chunk_id}.md"
        file_path.write_text(chunk.text, encoding="utf-8")
        with sqlite3.connect(self.sqlite_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO chunks (chunk_id, file_path, metadata_json) "
                "VALUES (?, ?, ?)",
                (chunk.chunk_id, str(file_path), json.dumps(chunk.metadata)),
            )

    def get(self, chunk_id: str) -> Optional[Chunk]:
        with sqlite3.connect(self.sqlite_path) as conn:
            row = conn.execute(
                "SELECT file_path, metadata_json FROM chunks WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()
        if not row:
            return None
        file_path, metadata_json = row
        text = Path(file_path).read_text(encoding="utf-8")
        return Chunk(chunk_id=chunk_id, text=text, metadata=json.loads(metadata_json))

    def query_metadata(self, **filters) -> list[str]:
        """Return chunk_ids matching all given metadata filters (exact match)."""
        # Simple v1: pull all, filter in Python. Optimize later if needed.
        with sqlite3.connect(self.sqlite_path) as conn:
            rows = conn.execute("SELECT chunk_id, metadata_json FROM chunks").fetchall()
        results = []
        for chunk_id, metadata_json in rows:
            md = json.loads(metadata_json)
            if all(md.get(k) == v for k, v in filters.items()):
                results.append(chunk_id)
        return results

    def delete(self, chunk_id: str) -> None:
        with sqlite3.connect(self.sqlite_path) as conn:
            row = conn.execute(
                "SELECT file_path FROM chunks WHERE chunk_id = ?", (chunk_id,)
            ).fetchone()
            if row:
                Path(row[0]).unlink(missing_ok=True)
                conn.execute("DELETE FROM chunks WHERE chunk_id = ?", (chunk_id,))