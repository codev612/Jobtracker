"""Database layer for the job tracker application."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

# Default status options for job applications
STATUSES = ["wishlist", "applying", "applied", "interviewing", "offer", "rejected", "accepted"]

DATABASE_PATH = Path(__file__).parent.parent / "jobs.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'applied',
            applied_date TEXT,
            salary TEXT,
            location TEXT,
            url TEXT,
            description TEXT,
            notes TEXT,
            tailored_resume TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    # Add description column for existing databases
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN description TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    # Add tailored_resume column for existing databases
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN tailored_resume TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.close()


def add_job(
    company: str,
    position: str,
    status: str = "applied",
    applied_date: Optional[str] = None,
    salary: Optional[str] = None,
    location: Optional[str] = None,
    url: Optional[str] = None,
    description: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """Add a new job application. Returns the new job ID."""
    now = datetime.now().isoformat()
    applied_date = applied_date or datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO jobs (company, position, status, applied_date, salary, location, url, description, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (company, position, status, applied_date, salary, location, url, description, notes, now, now),
    )
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return job_id


def get_all_jobs(
    status_filter: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,
    description: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[dict]:
    """Get all jobs, optionally filtered by status, company, position, description, and date range."""
    conn = get_connection()
    conditions = []
    values = []
    if status_filter:
        conditions.append("status = ?")
        values.append(status_filter)
    if company and company.strip():
        conditions.append("company LIKE ?")
        values.append(f"%{company.strip()}%")
    if position and position.strip():
        conditions.append("position LIKE ?")
        values.append(f"%{position.strip()}%")
    if description and description.strip():
        conditions.append("description LIKE ?")
        values.append(f"%{description.strip()}%")
    if date_from and date_from.strip():
        conditions.append("applied_date >= ?")
        values.append(date_from.strip())
    if date_to and date_to.strip():
        conditions.append("applied_date <= ?")
        values.append(date_to.strip())
    where = " AND ".join(conditions) if conditions else "1=1"
    rows = conn.execute(
        f"SELECT * FROM jobs WHERE {where} ORDER BY updated_at DESC",
        values,
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_job(job_id: int) -> Optional[dict]:
    """Get a single job by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_job(
    job_id: int,
    company: Optional[str] = None,
    position: Optional[str] = None,
    status: Optional[str] = None,
    applied_date: Optional[str] = None,
    salary: Optional[str] = None,
    location: Optional[str] = None,
    url: Optional[str] = None,
    description: Optional[str] = None,
    notes: Optional[str] = None,
    tailored_resume: Optional[str] = None,
) -> bool:
    """Update a job. Returns True if updated, False if not found."""
    job = get_job(job_id)
    if not job:
        return False

    updates = []
    values = []
    if company is not None:
        updates.append("company = ?")
        values.append(company)
    if position is not None:
        updates.append("position = ?")
        values.append(position)
    if status is not None:
        updates.append("status = ?")
        values.append(status)
    if applied_date is not None:
        updates.append("applied_date = ?")
        values.append(applied_date)
    if salary is not None:
        updates.append("salary = ?")
        values.append(salary)
    if location is not None:
        updates.append("location = ?")
        values.append(location)
    if url is not None:
        updates.append("url = ?")
        values.append(url)
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    if notes is not None:
        updates.append("notes = ?")
        values.append(notes)
    if tailored_resume is not None:
        updates.append("tailored_resume = ?")
        values.append(tailored_resume)

    if not updates:
        return True

    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(job_id)

    conn = get_connection()
    conn.execute(
        f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?",
        values,
    )
    conn.commit()
    conn.close()
    return True


def delete_job(job_id: int) -> bool:
    """Delete a job. Returns True if deleted, False if not found."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def search_jobs(query: str) -> list[dict]:
    """Search jobs by company, position, notes, or description."""
    conn = get_connection()
    pattern = f"%{query}%"
    rows = conn.execute(
        """
        SELECT * FROM jobs
        WHERE company LIKE ? OR position LIKE ? OR notes LIKE ? OR description LIKE ?
        ORDER BY updated_at DESC
        """,
        (pattern, pattern, pattern, pattern),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    """Get application statistics by status."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
    ).fetchall()
    conn.close()
    return {row["status"]: row["count"] for row in rows}
