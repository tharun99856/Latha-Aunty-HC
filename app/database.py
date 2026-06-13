import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "phc_queue.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            opened_at   TEXT    NOT NULL,
            closed_at   TEXT,
            total_issued INTEGER DEFAULT 0,
            total_served INTEGER DEFAULT 0,
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS tokens (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL REFERENCES sessions(id),
            number          TEXT    NOT NULL,
            phone           TEXT,
            status          TEXT    NOT NULL DEFAULT 'waiting',
            issued_at       TEXT    NOT NULL,
            called_at       TEXT,
            served_at       TEXT,
            notified_3ahead INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS consultations (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id       INTEGER NOT NULL REFERENCES sessions(id),
            token_id         INTEGER NOT NULL REFERENCES tokens(id),
            duration_seconds INTEGER NOT NULL,
            completed_at     TEXT    NOT NULL
        );
    """)
    db.commit()
    db.close()
