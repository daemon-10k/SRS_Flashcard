# App/models/user.py
import sqlite3
import hashlib
import os

# Determine the base directory of the 'App' folder 
# Assumes 'user.py' is in 'App/models/', so 'App/' is its parent directory.
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(APP_DIR, "database")
USER_DB_PATH = os.path.join(DATABASE_DIR, "user.db")

def hash_password(password: str) -> str:
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def _ensure_user_table_exists():
    """Ensures the users table exists with the correct schema."""
    # This function can be called by register_user or authenticate_user
    # if table creation isn't strictly handled by main.py's _init_user_database
    # For now, main.py's _init_user_database handles table creation.
    # If this module were to be fully independent, it would create its table.
    pass # Assuming main.py handles initial table creation via _init_user_database

def register_user(username: str, password: str) -> bool:
    """
    Registers a new user with a hashed password.

    Args:
        username: The username to register.
        password: The plain text password.

    Returns:
        True if registration is successful, False otherwise (e.g., username exists).
    """
    os.makedirs(DATABASE_DIR, exist_ok=True) 
    hashed_pw = hash_password(password)
    try:
        with sqlite3.connect(USER_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                           (username, hashed_pw))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error as e:
        print(f"Database error during registration: {e}")
        return False

def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticates a user by comparing the hashed provided password
    with the stored hashed password.

    Args:
        username: The username to authenticate.
        password: The plain text password.

    Returns:
        True if authentication is successful, False otherwise.
    """
    os.makedirs(DATABASE_DIR, exist_ok=True)
    hashed_pw_attempt = hash_password(password)
    try:
        with sqlite3.connect(USER_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
        
        if row and row[0] == hashed_pw_attempt:
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database error during authentication: {e}")
        return False