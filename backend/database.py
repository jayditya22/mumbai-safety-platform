"""
database.py
-----------
Handles the SQLite connection for the entire backend.

We use a single shared connection rather than opening and closing
one per request. For SQLite this is fine — it's a local file, not
a network database. If we ever upgrade to PostgreSQL, only this
file needs to change.
"""

import sqlite3
import os

# Build the path to the database file relative to this file's location.
# os.path.dirname(__file__) = the backend/ folder
# Going one level up (..) lands us at the project root where the .db file lives
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "mumbai_safety.db")


def get_connection() -> sqlite3.Connection:
    """
    Opens and returns a SQLite connection.

    check_same_thread=False is required because FastAPI handles requests
    on multiple threads — without this flag SQLite would raise an error
    when two requests arrive at the same time.

    row_factory = sqlite3.Row makes each database row behave like a
    dictionary, so we can access columns by name (row["ward_name"])
    instead of by index (row[1]). This makes the code far more readable.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn