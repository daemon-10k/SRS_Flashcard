# App/handlers/auth_handler.py
from PyQt6.QtWidgets import QMessageBox # type: ignore
from models.user import register_user as model_register_user, authenticate_user as model_authenticate_user
import deck_manager
import os

DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../database")

def handle_login(main_window):
    """Handles the login submission."""
    username = main_window.login_username_lineEdit.text().strip()
    password = main_window.login_password_lineEdit.text()
    if not username or not password:
        QMessageBox.warning(main_window, "Input Error", "Enter username and password.")
        return
    if model_authenticate_user(username, password):
        # Initialize the user's deck database
        user_deck_db_path = os.path.join(DATABASE_DIR, f"{username}_decks.db")
        if not deck_manager.init_user_decks_database(user_deck_db_path):
            QMessageBox.critical(main_window, "Database Error", f"Could not initialize deck database for user '{username}'.")
            return

        # Set the user's deck database path in the main window
        main_window.user_deck_db_path = user_deck_db_path

        QMessageBox.information(main_window, "Success", f"Welcome, {username}!")
        main_window.login_username_lineEdit.clear()
        main_window.login_password_lineEdit.clear()
        main_window.show_dashboard_page()
    else:
        QMessageBox.warning(main_window, "Login Failed", "Incorrect username or password.")
        main_window.login_password_lineEdit.clear()

def handle_registration(main_window):
    """Handles the registration submission."""
    username = main_window.register_username_lineEdit.text().strip()
    password = main_window.register_password_lineEdit.text()
    confirm_password = main_window.register_passwordConfirm_lineEdit.text()
    if not username or not password or not confirm_password:
        QMessageBox.warning(main_window, "Input Error", "Fill all fields.")
        return
    if password != confirm_password:
        QMessageBox.warning(main_window, "Error", "Passwords do not match.")
        main_window.register_password_lineEdit.clear()
        main_window.register_passwordConfirm_lineEdit.clear()
        return
    if model_register_user(username, password):
        # Initialize the user's deck database
        user_deck_db_path = os.path.join(DATABASE_DIR, f"{username}_decks.db")
        if not deck_manager.init_user_decks_database(user_deck_db_path):
            QMessageBox.critical(main_window, "Database Error", f"Could not initialize deck database for user '{username}'.")
            return

        QMessageBox.information(main_window, "Success", "Account created! Please log in.")
        main_window.register_username_lineEdit.clear()
        main_window.register_password_lineEdit.clear()
        main_window.register_passwordConfirm_lineEdit.clear()
        main_window.show_login_page()
    else:
        QMessageBox.warning(main_window, "Error", "Username already exists or registration failed.")
        main_window.register_password_lineEdit.clear()
        main_window.register_passwordConfirm_lineEdit.clear()

def handle_logout(main_window):
    """Handles user logout."""
    reply = QMessageBox.question(main_window, "Logout", "Are you sure you want to log out?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        main_window.current_user = None
        main_window.user_deck_db_path = None  # Clear the user's deck database path
        main_window.show_login_page()
        QMessageBox.information(main_window, "Logged Out", "You have been logged out successfully.")