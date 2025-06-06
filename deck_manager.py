# App/deck_manager.py
import sqlite3
import os
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(APP_DIR, "database")
FINISHED_INTERVAL_THRESHOLD = 21  

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

def init_user_decks_database(user_deck_db_path: str) -> bool:
    """
    Initializes a new SQLite database for the user's decks and cards.

    Args:
        user_deck_db_path: The path to the user's deck database.

    Returns:
        True if successful, False if an error occurred.
    """
    try:
        os.makedirs(os.path.dirname(user_deck_db_path), exist_ok=True)
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()

            # Step 1: Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            # Step 2: Create 'decks' table and commit it
            cursor.execute(SQL_CREATE_DECKS_TABLE)

            # Step 3: Create 'cards' table
            cursor.execute(SQL_CREATE_CARDS_TABLE)

            conn.commit()
        print(f"Successfully initialized user decks database at {user_deck_db_path}.")
        return True
    except sqlite3.Error as e:
        print(f"Database Error: Could not initialize user decks database: {e}")
        return False
def import_deck_and_cards(user_deck_db_path: str, deck_name: str, cards_data: list):
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
        with sqlite3.connect(user_deck_db_path) as conn:
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

def get_deck_for_export(user_deck_db_path: str, deck_id: int) -> dict | None:
    """
    Fetches a deck's name and all its card data for exporting.

    Args:
        user_deck_db_path: Path to the user's deck database.
        deck_id: ID of the deck to export.

    Returns:
        A dictionary structured for export, or None if the deck is not found.
    """
    export_data = {}
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # First, get the deck name from the 'decks' table
            cursor.execute("SELECT name FROM decks WHERE id = ?", (deck_id,))
            deck_row = cursor.fetchone()
            
            if not deck_row:
                print(f"Error: No deck found with id {deck_id}")
                return None
                
            export_data['deck_name'] = deck_row['name']

            # Next, get all cards for that deck
            # We only export front and back to keep the format clean
            cursor.execute("SELECT front, back FROM cards WHERE deck_id = ?", (deck_id,))
            cards = [{"front": row["front"], "back": row["back"]} for row in cursor.fetchall()]
            export_data['cards'] = cards
            
    except sqlite3.Error as e:
        print(f"Database Error: Could not get deck for export (deck_id {deck_id}): {e}")
        return None
        
    return export_data

def get_all_decks(user_deck_db_path: str) -> list:
    """
    Retrieves all decks for the authenticated user.

    Args:
        user_deck_db_path: Path to the user's deck database.

    Returns:
        A list of decks.
    """
    decks = []
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM decks ORDER BY name ASC")
            decks = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database Error: Could not load decks from {user_deck_db_path}: {e}")
    return decks

def create_new_deck(user_deck_db_path: str, deck_name: str) -> bool:
    """
    Creates a new deck in the user's deck database.

    Args:
        user_deck_db_path: Path to the user's deck database.
        deck_name: Name of the new deck.

    Returns:
        True if successful, False otherwise.
    """
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO decks (name) VALUES (?)", (deck_name,))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Database Error: Deck name '{deck_name}' already exists in {user_deck_db_path}.")
        return False
    except sqlite3.Error as e:
        print(f"Database Error: Could not create deck '{deck_name}' in {user_deck_db_path}: {e}")
        return False

def get_cards_for_deck(user_deck_db_path: str, deck_id: int) -> list:
    """
    Fetches all cards for a given deck ID in the user's deck database.

    Args:
        user_deck_db_path: Path to the user's deck database.
        deck_id: ID of the deck.

    Returns:
        A list of cards.
    """
    cards = []
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT id, front, back FROM cards WHERE deck_id = ? ORDER BY id ASC", (deck_id,))
            cards = [{"id": row["id"], "front": row["front"], "back": row["back"]} for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database Error: Could not load cards for deck_id {deck_id} in {user_deck_db_path}: {e}")
    return cards

def add_card(user_deck_db_path: str, deck_id: int, front: str, back: str) -> bool:
    """
    Adds a new card to the specified deck in the user's deck database.

    Args:
        user_deck_db_path: Path to the user's deck database.
        deck_id: ID of the deck.
        front: Front text of the card.
        back: Back text of the card.

    Returns:
        True if successful, False otherwise.
    """
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cards (deck_id, front, back) VALUES (?, ?, ?)", (deck_id, front, back))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database Error: Could not add card to deck_id {deck_id} in {user_deck_db_path}: {e}")
        return False

def delete_card_by_id(user_deck_db_path: str, card_id: int) -> bool:
    """
    Deletes a card by its ID in the user's deck database.

    Args:
        user_deck_db_path: Path to the user's deck database.
        card_id: ID of the card.

    Returns:
        True if successful, False otherwise.
    """
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database Error: Could not delete card_id {card_id} in {user_deck_db_path}: {e}")
        return False
    
def update_card_content(user_deck_db_path: str, card_id: int, front: str, back: str):
    """Updates the front and back text of an existing card."""
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE cards SET front = ?, back = ? WHERE id = ?", 
                           (front, back, card_id))
            conn.commit()
            return conn.total_changes > 0 # True if a row was updated
    except sqlite3.Error as e:
        print(f"Database Error: Could not update card_id {card_id}: {e}")
        raise # Or return False
def get_due_cards(user_deck_db_path:str, deck_id: int, current_date_str: str):
    """Fetches cards due for review for a given deck_id up to the current_date_str."""
    cards = []
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
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

def update_card_srs_details(user_deck_db_path: str, card_id: int, new_due_date_str: str, 
                            new_interval: int, new_ease_factor: float, new_repetitions: int):
    """Updates the SRS details and due date of an existing card."""
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
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

def get_deck_statistics(user_deck_db_path: str, deck_id: int) -> dict:
    """
    Calculates statistics for a given deck, including total and finished cards.

    Args:
        user_deck_db_path: Path to the user's deck database.
        deck_id: ID of the deck.

    Returns:
        A dictionary with total_cards and finished_cards counts.
    """
    stats = {'total_cards': 0, 'finished_cards': 0}
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()
            # Get the total number of cards in the deck
            cursor.execute("SELECT COUNT(id) FROM cards WHERE deck_id = ?", (deck_id,))
            total_cards = cursor.fetchone()[0]
            stats['total_cards'] = total_cards

            if total_cards > 0:
                # Get the number of "finished" cards based on the interval threshold
                cursor.execute(
                    "SELECT COUNT(id) FROM cards WHERE deck_id = ? AND interval >= ?",
                    (deck_id, FINISHED_INTERVAL_THRESHOLD)
                )
                finished_cards = cursor.fetchone()[0]
                stats['finished_cards'] = finished_cards
    except sqlite3.Error as e:
        print(f"Database Error: Could not get stats for deck_id {deck_id}: {e}")
    return stats


def get_global_statistics(user_deck_db_path: str) -> dict:
    """
    Calculates statistics for the entire database.

    Args:
        user_deck_db_path: Path to the user's deck database.

    Returns:
        A dictionary with global statistics.
    """
    stats = {
        'total_decks': 0,
        'total_cards': 0,
        'finished_cards': 0,
        'due_today': 0
    }
    if not os.path.exists(user_deck_db_path):
        return stats
        
    try:
        with sqlite3.connect(user_deck_db_path) as conn:
            cursor = conn.cursor()
            
            # Get total decks
            cursor.execute("SELECT COUNT(id) FROM decks")
            stats['total_decks'] = cursor.fetchone()[0]
            
            # Get total cards
            cursor.execute("SELECT COUNT(id) FROM cards")
            stats['total_cards'] = cursor.fetchone()[0]
            
            # Get total "finished" (learned) cards
            cursor.execute(
                "SELECT COUNT(id) FROM cards WHERE interval >= ?",
                (FINISHED_INTERVAL_THRESHOLD,)
            )
            stats['finished_cards'] = cursor.fetchone()[0]
            
            # Get cards due for review today
            today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "SELECT COUNT(id) FROM cards WHERE due_date IS NULL OR due_date <= ?",
                (today_str,)
            )
            stats['due_today'] = cursor.fetchone()[0]
            
    except sqlite3.Error as e:
        print(f"Database Error: Could not get global stats: {e}")
        
    return stats