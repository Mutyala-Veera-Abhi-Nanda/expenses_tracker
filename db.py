"""Database setup and CRUD operations for expenses. Supports SQLite (local) and PostgreSQL (Supabase)."""

import os
from datetime import datetime
from pathlib import Path

# Default categories
DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Transport",
    "Utilities",
    "Shopping",
    "Entertainment",
    "Healthcare",
    "Rent/Mortgage",
    "Subscriptions",
    "Education",
    "Other",
]


def _get_database_url():
    """Get database URL from Streamlit secrets or environment."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    return None


def _use_postgres():
    """Check if we should use PostgreSQL (Supabase) instead of SQLite."""
    return _get_database_url() is not None


def _prepare_postgres_url(url: str) -> str:
    """Ensure connection URL has sslmode=require for Supabase."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}sslmode=require"


def get_connection():
    """Get a database connection (SQLite or Postgres)."""
    if _use_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor

        url = _get_database_url()
        url = _prepare_postgres_url(url)
        conn = psycopg2.connect(
            url,
            cursor_factory=RealDictCursor,
            connect_timeout=10,
        )
        return conn

    # SQLite fallback
    import sqlite3

    DB_PATH = Path(__file__).parent / "expenses.db"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _dict_row(row):
    """Convert DB row to dict (handles both sqlite3.Row and RealDictRow)."""
    return dict(row) if hasattr(row, "keys") else dict(zip(row.keys(), row))


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection()
    try:
        if _use_postgres():
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        amount REAL NOT NULL,
                        category TEXT NOT NULL,
                        date TEXT NOT NULL,
                        description TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


def add_expense(amount: float, category: str, date: str, description: str = "") -> int:
    """Add a new expense. Returns the created expense id."""
    conn = get_connection()
    created_at = datetime.utcnow().isoformat()

    try:
        if _use_postgres():
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO expenses (amount, category, date, description, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (amount, category, date, description or "", created_at),
            )
            expense_id = cursor.fetchone()["id"]
        else:
            cursor = conn.execute(
                """
                INSERT INTO expenses (amount, category, date, description, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (amount, category, date, description or "", created_at),
            )
            expense_id = cursor.lastrowid

        conn.commit()
        return expense_id
    finally:
        conn.close()


def get_all_expenses(date_from: str | None = None, date_to: str | None = None):
    """Get all expenses, optionally filtered by date range."""
    conn = get_connection()
    param_style = "%s" if _use_postgres() else "?"

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if date_from:
        query += f" AND date >= {param_style}"
        params.append(date_from)
    if date_to:
        query += f" AND date <= {param_style}"
        params.append(date_to)

    query += " ORDER BY date DESC, id DESC"

    try:
        if _use_postgres():
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
        else:
            rows = conn.execute(query, params).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_expense(expense_id: int) -> bool:
    """Delete an expense by id. Returns True if deleted."""
    conn = get_connection()
    param_style = "%s" if _use_postgres() else "?"

    try:
        if _use_postgres():
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM expenses WHERE id = {param_style}", (expense_id,))
            deleted = cursor.rowcount > 0
        else:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            deleted = cursor.rowcount > 0

        conn.commit()
        return deleted
    finally:
        conn.close()
