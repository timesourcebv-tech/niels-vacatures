"""SQLite-laag voor vacatures. Dedup op (source, source_id)."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Iterable

DB_PATH = Path(__file__).parent / "data" / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    url TEXT NOT NULL,
    description TEXT,
    posted_at TEXT,
    discovered_at TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    status TEXT DEFAULT 'new',
    notes TEXT,
    UNIQUE(source, source_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_discovered ON jobs(discovered_at DESC);
"""


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_jobs(jobs: Iterable[dict]) -> tuple[int, int]:
    """Insert nieuwe vacatures. Retourneert (inserted, skipped)."""
    inserted = 0
    skipped = 0
    now = datetime.utcnow().isoformat(timespec="seconds")
    with get_conn() as conn:
        for job in jobs:
            try:
                conn.execute(
                    """
                    INSERT INTO jobs (source, source_id, title, company, location,
                                      url, description, posted_at, discovered_at, score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job["source"],
                        job["source_id"],
                        job["title"],
                        job.get("company"),
                        job.get("location"),
                        job["url"],
                        job.get("description"),
                        job.get("posted_at"),
                        now,
                        job.get("score", 0),
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                if "score" in job:
                    conn.execute(
                        "UPDATE jobs SET score = ? WHERE source = ? AND source_id = ?",
                        (job["score"], job["source"], job["source_id"]),
                    )
                skipped += 1
    return inserted, skipped


def update_status(job_id: int, status: str, notes: str | None = None) -> None:
    with get_conn() as conn:
        if notes is not None:
            conn.execute(
                "UPDATE jobs SET status = ?, notes = ? WHERE id = ?",
                (status, notes, job_id),
            )
        else:
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))


def fetch_jobs(
    min_score: int = 0,
    statuses: list[str] | None = None,
    limit: int = 500,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM jobs WHERE score >= ?"
    params: list = [min_score]
    if statuses:
        placeholders = ",".join("?" for _ in statuses)
        query += f" AND status IN ({placeholders})"
        params.extend(statuses)
    query += " ORDER BY score DESC, discovered_at DESC LIMIT ?"
    params.append(limit)
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def stats() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) AS new_count,
                SUM(CASE WHEN status='interesting' THEN 1 ELSE 0 END) AS interesting_count,
                SUM(CASE WHEN status='applied' THEN 1 ELSE 0 END) AS applied_count,
                SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) AS rejected_count,
                MAX(discovered_at) AS last_run
            FROM jobs
            """
        ).fetchone()
        return dict(row) if row else {}
