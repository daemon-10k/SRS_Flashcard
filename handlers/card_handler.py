# App/handlers/card_handler.py
from PyQt6.QtWidgets import QMessageBox # type: ignore
from main import EditCardDialog  # Assuming EditCardDialog is in main.py
import deck_manager

def handle_add_new_card(main_window):
    """Handles adding a new card to the current deck."""
    if main_window.current_deck_id is None:
        QMessageBox.warning(main_window, "Error", "No deck selected.")
        return
    dialog = EditCardDialog("", "", main_window)
    dialog.setWindowTitle("Add New Card")
    if dialog.exec():
        front, back = dialog.get_data()
        if front and back:
            try:
                print(f"Adding card with front: {front}, back: {back} to deck ID: {main_window.current_deck_id}")
                deck_manager.add_card(main_window.user_deck_db_path, main_window.current_deck_id, front, back)
                main_window._display_deck_cards_content()
            except Exception as e:
                QMessageBox.critical(main_window, "Database Error", f"Could not add card: {e}")
        else:
            QMessageBox.warning(main_window, "Input Error", "Front and Back cannot be empty.")

def handle_edit_card(main_window, card_id, current_front, current_back):
    """Handles editing an existing card."""
    if card_id is None:
        return
    dialog = EditCardDialog(current_front, current_back, main_window)
    if dialog.exec():
        front, back = dialog.get_data()
        if front and back:
            try:
                if deck_manager.update_card_content(main_window.user_deck_db_path, card_id, front, back):
                    main_window._display_deck_cards_content()
                else:
                    QMessageBox.warning(main_window, "Update Failed", "Could not update card.")
            except Exception as e:
                QMessageBox.critical(main_window, "Database Error", f"Could not update card: {e}")
        else:
            QMessageBox.warning(main_window, "Input Error", "Front and Back cannot be empty.")

def handle_delete_card(main_window, card_id):
    """Handles deleting a card."""
    if card_id is None:
        return
    reply = QMessageBox.question(main_window, "Delete Card", "Delete this card?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                 QMessageBox.StandardButton.No)
    if reply == QMessageBox.StandardButton.Yes:
        try:
            if deck_manager.delete_card_by_id(main_window.user_deck_db_path, card_id):
                main_window._display_deck_cards_content()
            else:
                QMessageBox.warning(main_window, "Delete Failed", "Could not delete card.")
        except Exception as e:
            QMessageBox.critical(main_window, "Database Error", f"Could not delete card: {e}")