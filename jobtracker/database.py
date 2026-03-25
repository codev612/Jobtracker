"""Database layer for the job tracker application."""

import sqlite3
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit
from typing import Optional

from .paths import BASE_PATH
from .profile_manager import get_profile_database_path

# Default status options for job applications
STATUSES = ["wishlist", "applying", "applied", "interviewing", "offer", "rejected", "accepted"]


def get_database_path() -> Path:
    """Get the database path for the current profile."""
    return get_profile_database_path()


# For backward compatibility - use get_database_path() for dynamic access
# This is evaluated at import time; use get_database_path() for current profile
DATABASE_PATH = BASE_PATH / "jobs.db"  # Legacy default, use get_database_path() instead


def get_connection() -> sqlite3.Connection:
    """Get a database connection. Ensures database is initialized."""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure profile directory exists
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    # Ensure table exists (in case init_db wasn't called for this profile)
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
            applied_resume_path TEXT,
            cover_letter_path TEXT,
            applied_resume_text TEXT,
            cover_letter_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure profile directory exists
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
            applied_resume_path TEXT,
            cover_letter_path TEXT,
            applied_resume_text TEXT,
            cover_letter_text TEXT,
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

    # Add applied_resume_path column for existing databases
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN applied_resume_path TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add cover_letter_path column for existing databases
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN cover_letter_path TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add applied_resume_text column for existing databases
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN applied_resume_text TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add cover_letter_text column for existing databases
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN cover_letter_text TEXT")
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
    applied_resume_path: Optional[str] = None,
    cover_letter_path: Optional[str] = None,
    applied_resume_text: Optional[str] = None,
    cover_letter_text: Optional[str] = None,
) -> int:
    """Add a new job application. Returns the new job ID."""
    now = datetime.now().isoformat()
    applied_date = applied_date or datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO jobs (
            company, position, status, applied_date, salary, location, url, description, notes,
            applied_resume_path, cover_letter_path,
            applied_resume_text, cover_letter_text,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company,
            position,
            status,
            applied_date,
            salary,
            location,
            url,
            description,
            notes,
            applied_resume_path,
            cover_letter_path,
            applied_resume_text,
            cover_letter_text,
            now,
            now,
        ),
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
    applied_resume_path: Optional[str] = None,
    cover_letter_path: Optional[str] = None,
    applied_resume_text: Optional[str] = None,
    cover_letter_text: Optional[str] = None,
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

    if applied_resume_path is not None:
        updates.append("applied_resume_path = ?")
        values.append(applied_resume_path)

    if cover_letter_path is not None:
        updates.append("cover_letter_path = ?")
        values.append(cover_letter_path)

    if applied_resume_text is not None:
        updates.append("applied_resume_text = ?")
        values.append(applied_resume_text)

    if cover_letter_text is not None:
        updates.append("cover_letter_text = ?")
        values.append(cover_letter_text)

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


def _url_variants(url: str) -> set[str]:
    """Return a set of normalized URL variants for duplicate detection.

    Normalization is intentionally simple:
    - ignores scheme (http/https)
    - strips trailing slash
    - ignores fragment
    - includes both canonical (no query) and full (with query)
    - includes both with and without leading 'www.'

    The returned strings are *not* valid URLs; they are comparable keys.
    """
    url = (url or "").strip()
    if not url:
        return set()

    # Make urlsplit treat bare domains as netloc.
    to_parse = url if "://" in url else f"https://{url}"
    parts = urlsplit(to_parse)

    netloc = (parts.netloc or "").strip().lower()
    path = (parts.path or "").rstrip("/")
    query = (parts.query or "").strip()

    if not netloc:
        # Fallback: compare on a very basic cleaned string.
        cleaned = url.strip().lower().rstrip("/")
        return {cleaned, cleaned.split("#", 1)[0].split("?", 1)[0]}

    netloc_variants = {netloc}
    if netloc.startswith("www.") and len(netloc) > 4:
        netloc_variants.add(netloc[4:])

    variants: set[str] = set()
    for host in netloc_variants:
        canonical = f"{host}{path}"
        variants.add(canonical)
        if query:
            variants.add(f"{canonical}?{query}")

    return variants


def job_url_exists(url: str, exclude_job_id: Optional[int] = None) -> bool:
    """Return True if a job with the given URL already exists.

    Used by the GUI to flag duplicate job URLs while typing.
    """
    input_variants = _url_variants(url)
    if not input_variants:
        return False

    conn = get_connection()
    try:
        if exclude_job_id is not None:
            rows = conn.execute(
                "SELECT url FROM jobs WHERE url IS NOT NULL AND id != ?",
                (exclude_job_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT url FROM jobs WHERE url IS NOT NULL"
            ).fetchall()

        for row in rows:
            existing_url = row[0]
            if not existing_url:
                continue
            if input_variants.intersection(_url_variants(str(existing_url))):
                return True
        return False
    finally:
        conn.close()
