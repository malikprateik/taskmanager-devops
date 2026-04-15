"""Database connection and initialization for Task Manager."""
import sqlite3
from flask import g, current_app

# Shared in-memory connection for testing
# (in-memory SQLite creates a new DB per connection, so we share one)
_shared_memory_db = None


def get_db(app=None):
    """Get a database connection for the current request context.

    Stores the connection in Flask's g object so it is reused
    within the same request and properly closed afterwards.
    For in-memory databases (testing), uses a shared connection
    so data persists across requests.
    """
    if "db" not in g:
        target_app = app or current_app
        db_path = target_app.config["DATABASE"]

        if db_path == ":memory:":
            global _shared_memory_db
            if _shared_memory_db is None:
                _shared_memory_db = sqlite3.connect(
                    ":memory:",
                    detect_types=sqlite3.PARSE_DECLTYPES,
                    check_same_thread=False,
                )
                _shared_memory_db.row_factory = sqlite3.Row
                _create_tables(_shared_memory_db)
            g.db = _shared_memory_db
        else:
            g.db = sqlite3.connect(
                db_path,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row

    return g.db


def close_db(exception=None):
    """Close the database connection at the end of a request.

    For in-memory (test) databases the connection is kept alive
    globally so data persists between requests.
    """
    db = g.pop("db", None)
    # Only close file-based connections; the shared memory
    # connection stays open for the entire test session
    if db is not None and db is not _shared_memory_db:
        db.close()


def reset_memory_db():
    """Reset the shared in-memory database (used between tests)."""
    global _shared_memory_db
    if _shared_memory_db is not None:
        try:
            _shared_memory_db.execute("DELETE FROM tasks")
            _shared_memory_db.commit()
        except Exception:
            pass


def _create_tables(db):
    """Create the tasks table if it does not already exist."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()


def init_db(app):
    """Initialise the database schema on application startup."""
    with app.app_context():
        db_path = app.config["DATABASE"]
        if db_path != ":memory:":
            db = get_db(app)
            _create_tables(db)
