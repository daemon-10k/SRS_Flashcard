# App/deck_manager.py
import sqlite3
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(APP_DIR, "database")
DB_DECKS_PATH = os.path.join(DATABASE_DIR, "decks.db")

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
SQL_INSERT_CARD_TEMPLATE = """
INSERT INTO cards (deck_id, front, back, due_date, interval, ease_factor, repetitions)
VALUES (?, ?, ?, ?, ?, ?, ?)"""

def init_decks_database():
    os.makedirs(DATABASE_DIR, exist_ok=True)
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL_CREATE_DECKS_TABLE)
            cursor.execute(SQL_CREATE_CARDS_TABLE)
            conn.commit()
        print("Decks database initialized successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Database Error: Could not initialize decks database: {e}")
        return False

def get_all_decks():
    decks = []
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            conn.row_factory = sqlite3.Row # To access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM decks ORDER BY name ASC")
            decks = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database Error: Could not load decks: {e}")
    return decks # Returns list of dicts

def create_new_deck(deck_name: str):
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO decks (name) VALUES (?)", (deck_name,))
            conn.commit()
        return True
    except sqlite3.IntegrityError: raise
    except sqlite3.Error as e: print(f"Database error creating deck: {e}"); raise

def import_deck_and_cards(deck_name: str, cards_data: list):
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO decks (name) VALUES (?)", (deck_name,))
            deck_id = cursor.lastrowid
            for card_item in cards_data:
                if not (isinstance(card_item, dict) and "front" in card_item and "back" in card_item): continue
                front, back = card_item.get("front", ""), card_item.get("back", "")
                due, interval, ease, reps = card_item.get("due_date"), card_item.get("interval", 1), card_item.get("ease_factor", 2.5), card_item.get("repetitions", 0)
                cursor.execute(SQL_INSERT_CARD_TEMPLATE, (deck_id, front, back, due, interval, ease, reps))
            conn.commit()
        return True
    except sqlite3.IntegrityError: raise
    except sqlite3.Error as e: print(f"Database error importing deck data: {e}"); raise

# --- New functions for card management ---
def get_cards_for_deck(deck_id: int):
    """Fetches all cards for a given deck_id."""
    cards = []
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            conn.row_factory = sqlite3.Row # Access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT id, front, back FROM cards WHERE deck_id = ? ORDER BY id ASC", (deck_id,))
            cards = [{"id": row["id"], "front": row["front"], "back": row["back"]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database Error: Could not load cards for deck_id {deck_id}: {e}")
    return cards # Returns list of dicts

def add_card(deck_id: int, front: str, back: str):
    """Adds a new card to the specified deck."""
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            # Using default values for SRS parameters initially
            cursor.execute("INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)", 
                           (deck_id, front, back))
            conn.commit()
            return cursor.lastrowid # Return the new card's ID
    except sqlite3.Error as e:
        print(f"Database Error: Could not add card to deck_id {deck_id}: {e}")
        raise # Or return None/False

def update_card_content(card_id: int, front: str, back: str):
    """Updates the front and back text of an existing card."""
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cards SET front = ?, back = ? WHERE id = ?", 
                           (front, back, card_id))
            conn.commit()
            return conn.total_changes > 0 # True if a row was updated
    except sqlite3.Error as e:
        print(f"Database Error: Could not update card_id {card_id}: {e}")
        raise # Or return False

def delete_card_by_id(card_id: int):
    """Deletes a card by its ID."""
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            conn.commit()
            return conn.total_changes > 0 # True if a row was deleted
    except sqlite3.Error as e:
        print(f"Database Error: Could not delete card_id {card_id}: {e}")
        raise # Or return False

def import_deck_and_cards(deck_name: str, cards_data: list):
    """
    Imports a new deck and its cards into the database.
    
    Args:
        deck_name: The name of the deck.
        cards_data: A list of card dictionaries.

    Returns:
        True if successful.
        
    Raises:
        sqlite3.IntegrityError: If the deck name already exists.
        sqlite3.Error: For other database errors.
    """
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("INSERT INTO decks (name) VALUES (?)", (deck_name,))
            deck_id = cursor.lastrowid

            for card_item in cards_data:
                # Basic validation, import_utils should have done more thorough checks
                if not (isinstance(card_item, dict) and 
                        "front" in card_item and "back" in card_item):
                    print(f"Skipping invalid card data during DB import: {card_item}")
                    continue 
                
                front = card_item.get("front", "")
                back = card_item.get("back", "")
                due_date = card_item.get("due_date") 
                interval = card_item.get("interval", 1)
                ease_factor = card_item.get("ease_factor", 2.5)
                repetitions = card_item.get("repetitions", 0)
                
                cursor.execute(SQL_INSERT_CARD_TEMPLATE, 
                               (deck_id, front, back, due_date, interval, ease_factor, repetitions))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        raise # Let the caller handle this
    except sqlite3.Error as e: 
        print(f"Database error importing deck data for '{deck_name}': {e}")
        raise
    
def get_due_cards(deck_id: int, current_date_str: str):
    """Fetches cards due for review for a given deck_id up to the current_date_str."""
    cards = []
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Fetch cards where due_date is today or in the past, or never reviewed (NULL due_date)
            cursor.execute("""
                SELECT id, front, back, repetitions, ease_factor, interval 
                FROM cards 
                WHERE deck_id = ? AND (due_date IS NULL OR due_date <= ?)
                ORDER BY due_date ASC, RANDOM()
            """, (deck_id, current_date_str))
            cards = [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database Error (get_due_cards for deck_id {deck_id}): {e}")
    return cards

def update_card_srs_details(card_id: int, new_due_date_str: str, 
                            new_interval: int, new_ease_factor: float, new_repetitions: int):
    """Updates the SRS details and due date of an existing card."""
    try:
        with sqlite3.connect(DB_DECKS_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE cards 
                SET due_date = ?, interval = ?, ease_factor = ?, repetitions = ? 
                WHERE id = ?
            """, (new_due_date_str, new_interval, new_ease_factor, new_repetitions, card_id))
            conn.commit()
            return conn.total_changes > 0
    except sqlite3.Error as e:
        print(f"Database Error (update_card_srs_details for card_id {card_id}): {e}")
        raise    