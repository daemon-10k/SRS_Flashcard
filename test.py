import sqlite3
SQL_CREATE_DECKS_TABLE = """
CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)"""

SQL_CREATE_CARDS_TABLE = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_id INTEGER NOT NULL,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    due_date TEXT,
    interval INTEGER DEFAULT 1,
    ease_factor REAL DEFAULT 2.5,
    repetitions INTEGER DEFAULT 0,
    FOREIGN KEY(deck_id) REFERENCES decks(id) ON DELETE CASCADE
)"""

with sqlite3.connect("test_cards.db") as conn:
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS cards")
    cursor.execute(SQL_CREATE_DECKS_TABLE)
    cursor.execute(SQL_CREATE_CARDS_TABLE)
    cursor.execute("PRAGMA table_info(cards)")
    for row in cursor.fetchall():
        print(row)
