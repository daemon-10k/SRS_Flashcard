# App/handlers/deck_handler.py
import sqlite3
import json
import os
from PyQt6.QtWidgets import QInputDialog, QMessageBox, QFileDialog # type: ignore # type: ignore
import deck_manager
import import_utils, export_utils

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
        
def handle_export_deck(main_window):
    """
    Handles exporting the currently open deck to a JSON file.
    """
    if main_window.current_deck_id is None or not main_window.user_deck_db_path:
        QMessageBox.warning(main_window, "Error", "No deck is currently open to export.")
        return

    # 1. Get the deck's data from the database manager
    deck_data = deck_manager.get_deck_for_export(
        main_window.user_deck_db_path, main_window.current_deck_id
    )
    
    if not deck_data:
        QMessageBox.critical(main_window, "Error", "Could not retrieve deck data for export.")
        return

    # Create a safe, default filename from the deck name
    deck_name = deck_data.get('deck_name', 'deck')
    default_filename = "".join(c for c in deck_name if c.isalnum() or c in (' ', '_')).rstrip() + ".json"

    # 2. Open a "Save File" dialog to let the user choose a location
    file_path, _ = QFileDialog.getSaveFileName(
        main_window,
        "Export Deck As",
        os.path.join(main_window.APP_DIR, default_filename),
        "JSON Files (*.json);;All Files (*)"
    )

    if not file_path:
        return # User cancelled the dialog

    # 3. Call the export utility to write the data to the chosen file
    if export_utils.export_deck_to_json(deck_data, file_path):
        QMessageBox.information(main_window, "Success", f"Deck '{deck_name}' was successfully exported.")
    else:
        QMessageBox.critical(main_window, "Export Failed", "An error occurred while exporting the deck.")