# App/handlers/deck_handler.py
import sqlite3
import json
from PyQt6.QtWidgets import QInputDialog, QMessageBox, QFileDialog # type: ignore # type: ignore
import deck_manager
import import_utils

def handle_create_new_deck(main_window):
    """Handles the creation of a new deck."""
    deck_name, ok = QInputDialog.getText(main_window, "Create New Deck", "Enter deck name:")
    if ok and deck_name.strip():
        deck_name = deck_name.strip()
        try:
            deck_manager.create_new_deck(main_window.user_deck_db_path, deck_name)
            QMessageBox.information(main_window, "Success", f"Deck '{deck_name}' created.")
            main_window._display_my_decks_list_content()
        except sqlite3.IntegrityError:
            QMessageBox.warning(main_window, "Error", f"A deck named '{deck_name}' already exists.")
        except Exception as e:
            QMessageBox.critical(main_window, "Database Error", f"Could not create deck: {e}")
    elif ok:
        QMessageBox.warning(main_window, "Input Error", "Deck name cannot be empty.")

def handle_import_deck(main_window):
    """Handles importing a deck from a file."""
    file_path, _ = QFileDialog.getOpenFileName(main_window, "Import Deck File", main_window.APP_DIR, "JSON Files (*.json);;All Files (*)")
    if not file_path:
        return
    deck_name_for_error = "from file"
    try:
        if file_path.endswith('.json'):
            deck_name, cards_data = import_utils.parse_json_deck_file(file_path)
            deck_name_for_error = deck_name
            deck_manager.import_deck_and_cards(main_window.user_deck_db_path, deck_name, cards_data)
            QMessageBox.information(main_window, "Success", f"Deck '{deck_name}' imported.")
            main_window._display_my_decks_list_content()
        else:
            QMessageBox.warning(main_window, "Unsupported Format", "Only JSON currently supported.")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        QMessageBox.critical(main_window, "Import Error", str(e))
    except sqlite3.IntegrityError:
        QMessageBox.warning(main_window, "Import Error", f"Deck '{deck_name_for_error}' already exists.")
    except Exception as e:
        QMessageBox.critical(main_window, "Import Failed", f"Error: {e}")