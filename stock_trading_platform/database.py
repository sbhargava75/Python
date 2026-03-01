import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "trading.db")

STARTING_CASH = 100_000.00


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cash        REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS holdings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT NOT NULL UNIQUE,
            shares      INTEGER NOT NULL DEFAULT 0,
            avg_cost    REAL NOT NULL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT NOT NULL,
            side        TEXT NOT NULL CHECK(side IN ('BUY', 'SELL')),
            shares      INTEGER NOT NULL,
            price       REAL NOT NULL,
            total       REAL NOT NULL,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed the portfolio with starting cash if empty
    row = conn.execute("SELECT COUNT(*) AS cnt FROM portfolio").fetchone()
    if row["cnt"] == 0:
        conn.execute("INSERT INTO portfolio (cash) VALUES (?)", (STARTING_CASH,))

    conn.commit()
    conn.close()
