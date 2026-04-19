# sqlite db setup and connection handling
import sqlite3
from flask import g, current_app

# shared connection for in-memory testing

_shared_memory_db = None


def get_db(app=None):
    # get or create db connection for current request
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
    # close db unless its the shared test one
    db = g.pop("db", None)

    if db is not None and db is not _shared_memory_db:
        db.close()


def reset_memory_db():
    # wipe tasks table between tests
    global _shared_memory_db
    if _shared_memory_db is not None:
        try:
            _shared_memory_db.execute("DELETE FROM tasks")
            _shared_memory_db.commit()
        except Exception:
            pass


def _create_tables(db):
    # create the tasks table
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
    # run table creation on startup
    with app.app_context():
        db_path = app.config["DATABASE"]
        if db_path != ":memory:":
            db = get_db(app)
            _create_tables(db)
