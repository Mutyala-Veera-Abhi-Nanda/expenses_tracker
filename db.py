"""SQLite database setup and CRUD operations for expenses."""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "expenses.db"

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


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_connection()
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
    conn.close()


def add_expense(amount: float, category: str, date: str, description: str = "") -> int:
    """Add a new expense. Returns the created expense id."""
    conn = get_connection()
    created_at = datetime.utcnow().isoformat()
    cursor = conn.execute(
        """
        INSERT INTO expenses (amount, category, date, description, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (amount, category, date, description or "", created_at),
    )
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def get_all_expenses(date_from: str | None = None, date_to: str | None = None):
    """Get all expenses, optionally filtered by date range."""
    conn = get_connection()
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)

    query += " ORDER BY date DESC, id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def delete_expense(expense_id: int) -> bool:
    """Delete an expense by id. Returns True if deleted."""
    conn = get_connection()
    cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
