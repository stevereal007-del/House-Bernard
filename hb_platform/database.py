"""SQLite database setup and connection management."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from . import config


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Execute all SQL migration files in order."""
    migration_dir = config.MIGRATIONS_DIR
    if not migration_dir.exists():
        return
    for sql_file in sorted(migration_dir.glob("*.sql")):
        conn.executescript(sql_file.read_text(encoding="utf-8"))


def init_db() -> None:
    """Create the database and run migrations."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        _run_migrations(conn)


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Yield a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
