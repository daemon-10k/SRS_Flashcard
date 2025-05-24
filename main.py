# App/main.py
import sys
import json 
import os
import sqlite3 
from datetime import datetime, timedelta # Import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QMessageBox, QVBoxLayout,
                             QPushButton, QLabel, QFileDialog, QLineEdit, QInputDialog, QScrollArea,
                             QDialog, QFormLayout, QTextEdit, QDialogButtonBox) 
from PyQt6.uic import loadUi
from PyQt6.QtCore import Qt

# Modular imports
from models.user import register_user as model_register_user, authenticate_user as model_authenticate_user
import deck_manager 
import import_utils 
from page_handlers import my_decks_ui
from page_handlers import card_display_ui 
from utils import srs_logic 

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(APP_DIR, "database")
UI_FILE_PATH = os.path.join(APP_DIR, "main.ui")

SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)"""

class EditCardDialog(QDialog): # No changes to this dialog
    def __init__(self, current_front, current_back, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Card")
        self.setMinimumWidth(300)
        self.layout = QFormLayout(self)
        self.front_text_edit = QTextEdit(current_front)
        self.front_text_edit.setPlaceholderText("Enter front text of the card")
        self.back_text_edit = QTextEdit(current_back)
        self.back_text_edit.setPlaceholderText("Enter back text of the card")
        self.layout.addRow("Front:", self.front_text_edit)
        self.layout.addRow("Back:", self.back_text_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
    def get_data(self):
        return self.front_text_edit.toPlainText().strip(), self.back_text_edit.toPlainText().strip()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        os.makedirs(DATABASE_DIR, exist_ok=True)
        if not os.path.exists(UI_FILE_PATH):
            QMessageBox.critical(None, "Error", f"UI file not found: {UI_FILE_PATH}")
            sys.exit(1)
        loadUi(UI_FILE_PATH, self)

        self.page_history = [] 
        self._navigating_back = False 
        self.current_deck_id = None 
        self.current_deck_name = None 

        # For review session
        self.current_review_deck_id = None
        self.review_cards_list = []
        self.current_review_card_index = -1
        self.current_review_card_data = None # Will store the full card dict (id, front, back, srs data)
        self.showing_answer = False

        self._connect_signals()
        self._init_user_database()
        if not deck_manager.init_decks_database():
            QMessageBox.critical(self, "Startup Error", "Could not initialize decks database.")
        
        self.main_stackedWidget.setCurrentWidget(self.login_page)
        self._update_all_back_button_states() 

    def _connect_signals(self):
        # (Existing connections ...)
        self.login_goToRegister_button.clicked.connect(self.show_register_page)
        self.login_submit_button.clicked.connect(self.handle_login_submission)
        if hasattr(self, 'register_goBackButton'): self.register_goBackButton.clicked.connect(self.handle_go_back)
        self.register_submit_button.clicked.connect(self.handle_register_submission)
        self.dashboard_goToReview_button.clicked.connect(self.start_review_session_for_current_deck) # Modified
        self.dashboard_goToMyDecks_button.clicked.connect(self.show_myDecks_page)
        
        if hasattr(self, 'review_goBackButton'): self.review_goBackButton.clicked.connect(self.handle_go_back) 
        if hasattr(self, 'review_showAnswer_button'): self.review_showAnswer_button.clicked.connect(self.handle_show_answer)
        if hasattr(self, 'review_easy_button'): self.review_easy_button.clicked.connect(lambda: self.handle_review_difficulty_selected(5)) # Quality 5
        if hasattr(self, 'review_medium_button'): self.review_medium_button.clicked.connect(lambda: self.handle_review_difficulty_selected(4)) # Quality 4
        if hasattr(self, 'review_hard_button'): self.review_hard_button.clicked.connect(lambda: self.handle_review_difficulty_selected(3)) # Quality 3 (adjust as needed)
        
        if hasattr(self, 'myDecks_goBackButton'): self.myDecks_goBackButton.clicked.connect(self.handle_go_back)
        if hasattr(self, 'myDecks_noDecks_create_button'): self.myDecks_noDecks_create_button.clicked.connect(self.handle_create_new_deck_button_click)
        if hasattr(self, 'myDecks_noDecks_import_button'): self.myDecks_noDecks_import_button.clicked.connect(self.handle_import_deck_button_click)
        if hasattr(self, 'myDecks_list_create_button'): self.myDecks_list_create_button.clicked.connect(self.handle_create_new_deck_button_click)
        if hasattr(self, 'myDecks_list_import_button'): self.myDecks_list_import_button.clicked.connect(self.handle_import_deck_button_click)
        if hasattr(self, 'card_list_goBackButton'): self.card_list_goBackButton.clicked.connect(self.handle_go_back_to_my_decks)
        if hasattr(self, 'card_list_add_card_button'): self.card_list_add_card_button.clicked.connect(self.handle_add_new_card_dialog)

    # ... (_init_user_database, _navigate_to_page, handle_go_back, _update_all_back_button_states, show_..._page methods) ...
    # ... (handle_login_submission, handle_register_submission) ...
    # ... (_display_my_decks_list_content, handle_create_new_deck_button_click, handle_import_deck_button_click) ...
    # ... (_display_deck_cards_content, handle_add_new_card_dialog, handle_edit_card_dialog, handle_delete_card_action) ...
    # (Make sure these are the latest versions from my previous full code response)

    def _init_user_database(self): # Ensure this method is present and correct
        user_db_path_for_init = os.path.join(DATABASE_DIR, "user.db")
        try:
            with sqlite3.connect(user_db_path_for_init) as conn:
                cursor = conn.cursor()
                cursor.execute(SQL_CREATE_USERS_TABLE)
                conn.commit()
            print("User database initialized successfully.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not initialize user database: {e}")
            sys.exit(1)

    def _navigate_to_page(self, target_page_widget: QWidget):
        current_active_widget = self.main_stackedWidget.currentWidget()
        if target_page_widget == current_active_widget: return
        if not self._navigating_back:
            if current_active_widget is not None:
                if not self.page_history or self.page_history[-1] != current_active_widget:
                    self.page_history.append(current_active_widget)
        self.main_stackedWidget.setCurrentWidget(target_page_widget)
        self._update_all_back_button_states()

    def handle_go_back(self): 
        if self.page_history:
            self._navigating_back = True
            previous_widget = self.page_history.pop()
            self.main_stackedWidget.setCurrentWidget(previous_widget)
            if previous_widget == self.myDecks_page: self._display_my_decks_list_content()
            if previous_widget == self.dashboard_page: self.current_review_deck_id = None # Clear review context
            self._navigating_back = False
            self._update_all_back_button_states()
        else: self._update_all_back_button_states()
    
    def handle_go_back_to_my_decks(self):
        self._navigating_back = True 
        self.current_review_deck_id = None # Clear review context when leaving card list
        self.show_myDecks_page() 
        self._navigating_back = False 
        if self.page_history and self.page_history[-1] == self.myDecks_page: pass 
        elif self.page_history and self.page_history[-1] == self.card_list_page: self.page_history.pop()

    def _update_all_back_button_states(self):
        buttons_to_check = ['register_goBackButton', 'review_goBackButton', 'myDecks_goBackButton']
        for btn_name in buttons_to_check:
            if hasattr(self, btn_name): self._update_back_button_state(getattr(self, btn_name))
        if hasattr(self, 'card_list_goBackButton'): 
            self.card_list_goBackButton.setEnabled(self.main_stackedWidget.currentWidget() == self.card_list_page)

    def _update_back_button_state(self, button_widget: QPushButton):
        if button_widget: button_widget.setEnabled(bool(self.page_history))
    
    def show_register_page(self): self._navigate_to_page(self.register_page)
    def show_login_page(self): self.page_history.clear(); self._navigate_to_page(self.login_page)
    def show_dashboard_page(self): self.current_review_deck_id = None; self.page_history.clear(); self._navigate_to_page(self.dashboard_page)
    
    def show_myDecks_page(self): self._display_my_decks_list_content(); self._navigate_to_page(self.myDecks_page)
    
    def show_card_list_page(self):
        if self.current_deck_id is None:
            QMessageBox.warning(self, "Error", "No deck selected."); self.show_myDecks_page(); return
        if hasattr(self, 'card_list_deck_name_label'):
            self.card_list_deck_name_label.setText(f"Deck: {self.current_deck_name}")
        self._display_deck_cards_content()
        self._navigate_to_page(self.card_list_page)

    def handle_login_submission(self):
        username = self.login_username_lineEdit.text().strip()
        password = self.login_password_lineEdit.text()
        if not username or not password: QMessageBox.warning(self, "Input Error", "Enter username and password."); return
        if model_authenticate_user(username, password):
            QMessageBox.information(self, "Success", f"Welcome, {username}!"); self.show_dashboard_page()
        else: QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")

    def handle_register_submission(self):
        username = self.register_username_lineEdit.text().strip()
        password = self.register_password_lineEdit.text()
        confirm_password = self.register_passwordConfirm_lineEdit.text()
        if not username or not password or not confirm_password: QMessageBox.warning(self, "Input Error", "Fill all fields."); return
        if password != confirm_password: QMessageBox.warning(self, "Error", "Passwords do not match."); return
        if model_register_user(username, password):
            QMessageBox.information(self, "Success", "Account created! Please log in."); self.show_login_page()
        else: QMessageBox.warning(self, "Error", "Username already exists or registration failed.")

    def _display_my_decks_list_content(self):
        if not all(hasattr(self, name) for name in ['myDecks_list_verticalLayout', 'myDecks_list_stackedWidget', 'myDecks_list_page', 'myDecks_noDecks_page']):
            QMessageBox.warning(self, "UI Error", "MyDecks page UI elements not fully loaded."); return
        my_decks_ui.populate_decks_list(
            deck_list_layout=self.myDecks_list_verticalLayout, list_stacked_widget=self.myDecks_list_stackedWidget,
            list_page_widget=self.myDecks_list_page, no_decks_page_widget=self.myDecks_noDecks_page,
            open_deck_callback=self.handle_open_deck
        )

    def handle_open_deck(self, deck_id: int, deck_name: str):
        self.current_deck_id = deck_id; self.current_deck_name = deck_name
        self.current_review_deck_id = deck_id # Set for potential review session
        self.show_card_list_page()

    def handle_create_new_deck_button_click(self):
        deck_name, ok = QInputDialog.getText(self, "Create New Deck", "Enter deck name:")
        if ok and deck_name.strip():
            deck_name = deck_name.strip()
            try:
                deck_manager.create_new_deck(deck_name)
                QMessageBox.information(self, "Success", f"Deck '{deck_name}' created.")
                self._display_my_decks_list_content() 
            except sqlite3.IntegrityError: QMessageBox.warning(self, "Error", f"A deck named '{deck_name}' already exists.")
            except Exception as e: QMessageBox.critical(self, "Database Error", f"Could not create deck: {e}")
        elif ok: QMessageBox.warning(self, "Input Error", "Deck name cannot be empty.")

    def handle_import_deck_button_click(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Deck File", APP_DIR, "JSON Files (*.json);;All Files (*)")
        if not file_path: return
        deck_name_for_error = "from file"
        try:
            if file_path.endswith('.json'):
                deck_name, cards_data = import_utils.parse_json_deck_file(file_path)
                deck_name_for_error = deck_name
                deck_manager.import_deck_and_cards(deck_name, cards_data)
                QMessageBox.information(self, "Success", f"Deck '{deck_name}' imported.")
                self._display_my_decks_list_content()
            else: QMessageBox.warning(self, "Unsupported Format", "Only JSON currently supported.")
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e: QMessageBox.critical(self, "Import Error", str(e))
        except sqlite3.IntegrityError: QMessageBox.warning(self, "Import Error", f"Deck '{deck_name_for_error}' already exists.")
        except Exception as e: QMessageBox.critical(self, "Import Failed", f"Error: {e}")

    def _display_deck_cards_content(self):
        if self.current_deck_id is None: return
        if not hasattr(self, 'card_list_verticalLayout'):
             QMessageBox.warning(self, "UI Error", "Card list UI elements not loaded."); return
        card_display_ui.populate_card_list(
            card_list_layout=self.card_list_verticalLayout, deck_id=self.current_deck_id,
            edit_card_callback=self.handle_edit_card_dialog, 
            delete_card_callback=self.handle_delete_card_action
        )

    def handle_add_new_card_dialog(self):
        if self.current_deck_id is None: QMessageBox.warning(self, "Error", "No deck selected."); return
        dialog = EditCardDialog("", "", self); dialog.setWindowTitle("Add New Card")
        if dialog.exec():
            front, back = dialog.get_data()
            if front and back:
                try: deck_manager.add_card(self.current_deck_id, front, back); self._display_deck_cards_content()
                except Exception as e: QMessageBox.critical(self, "Database Error", f"Could not add card: {e}")
            else: QMessageBox.warning(self, "Input Error", "Front and Back cannot be empty.")
    
    def handle_edit_card_dialog(self, card_id: int, current_front: str, current_back: str):
        if card_id is None: return
        dialog = EditCardDialog(current_front, current_back, self)
        if dialog.exec():
            front, back = dialog.get_data()
            if front and back:
                try:
                    if deck_manager.update_card_content(card_id, front, back): self._display_deck_cards_content()
                    else: QMessageBox.warning(self, "Update Failed", "Could not update card.")
                except Exception as e: QMessageBox.critical(self, "Database Error", f"Could not update card: {e}")
            else: QMessageBox.warning(self, "Input Error", "Front and Back cannot be empty.")

    def handle_delete_card_action(self, card_id: int):
        if card_id is None: return
        reply = QMessageBox.question(self, "Delete Card", "Delete this card?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if deck_manager.delete_card_by_id(card_id): self._display_deck_cards_content()
                else: QMessageBox.warning(self, "Delete Failed", "Could not delete card.")
            except Exception as e: QMessageBox.critical(self, "Database Error", f"Could not delete card: {e}")

    # --- Review Page Logic ---
    def start_review_session_for_current_deck(self):
        """Initiates a review session for the self.current_review_deck_id."""
        if self.current_review_deck_id is None:
            decks = deck_manager.get_all_decks()
            if not decks:
                QMessageBox.information(self, "Review", "No decks available to review.")
                self.show_dashboard_page()
                return
            deck_names = [d["name"] for d in decks]
            deck_name, ok = QInputDialog.getItem(self, "Select Deck", "Choose a deck to review:", deck_names, 0, False)
            if ok and deck_name:
                selected_deck_data = next((d for d in decks if d["name"] == deck_name), None)
                if selected_deck_data:
                    self.current_review_deck_id = selected_deck_data["id"]
            else: # User cancelled or no deck selected
                self.show_dashboard_page()
                return


        today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.review_cards_list = deck_manager.get_due_cards(self.current_review_deck_id, today_str)
        
        if not self.review_cards_list:
            QMessageBox.information(self, "Review Complete", "No cards due for review in this deck right now!")
            self.show_dashboard_page() # Or back to My Decks
            return

        self.current_review_card_index = 0
        self.showing_answer = False
        self._load_review_card()
        self._navigate_to_page(self.review_page)

    def show_review_page(self): # Overridden to ensure session is started if directly navigated
        if self.current_review_deck_id is None or not self.review_cards_list:
            # If trying to show review page without an active session, start one
            # (or redirect, here we try to start for the last selected deck if any)
            self.start_review_session_for_current_deck() 
        else:
            # A session is already active, just navigate
            self._navigate_to_page(self.review_page)


    def _load_review_card(self):
        """Loads the current card onto the review page UI."""
        if self.current_review_card_index < 0 or self.current_review_card_index >= len(self.review_cards_list):
            QMessageBox.information(self, "Review Complete", "You've reviewed all due cards in this session!")
            self.current_review_deck_id = None # Clear current review deck
            self.review_cards_list = []
            self.current_review_card_index = -1
            self.show_dashboard_page() # Or back to My Decks
            return

        self.current_review_card_data = self.review_cards_list[self.current_review_card_index]
        
        # Update UI elements (ensure these names exist in your review_page in ui.xml)
        if hasattr(self, 'review_cardDisplay_label'):
            if self.showing_answer:
                display_text = f"<b>Front:</b> {self.current_review_card_data['front']}\n\n<b>Back:</b> {self.current_review_card_data['back']}"
            else:
                display_text = f"<b>Front:</b> {self.current_review_card_data['front']}"
            self.review_cardDisplay_label.setText(display_text)
        
        if hasattr(self, 'review_showAnswer_button'):
            self.review_showAnswer_button.setVisible(not self.showing_answer)
        
        difficulty_buttons_visible = self.showing_answer
        if hasattr(self, 'review_easy_button'): self.review_easy_button.setVisible(difficulty_buttons_visible)
        if hasattr(self, 'review_medium_button'): self.review_medium_button.setVisible(difficulty_buttons_visible)
        if hasattr(self, 'review_hard_button'): self.review_hard_button.setVisible(difficulty_buttons_visible)
        
        # Update review page title if needed
        if hasattr(self, 'review_title_label'):
            self.review_title_label.setText(f"Reviewing Deck (Card {self.current_review_card_index + 1}/{len(self.review_cards_list)})")


    def handle_show_answer(self):
        self.showing_answer = True
        self._load_review_card()

    def handle_review_difficulty_selected(self, quality: int):
        if not self.current_review_card_data:
            return

        card = self.current_review_card_data
        reps = card.get('repetitions', 0)
        ef = card.get('ease_factor', 2.5)
        interval = card.get('interval', 1)

        new_reps, new_ef, new_interval_days = srs_logic.calculate_srs_update(quality, reps, ef, interval)
        
        new_due_date = datetime.now() + timedelta(days=new_interval_days)
        new_due_date_str = new_due_date.strftime("%Y-%m-%d %H:%M:%S")

        try:
            deck_manager.update_card_srs_details(card['id'], new_due_date_str, new_interval_days, new_ef, new_reps)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not update card SRS details: {e}")
            # Decide how to proceed: retry? skip?
            
        self.current_review_card_index += 1
        self.showing_answer = False # Reset for the next card
        self._load_review_card()
    
    def closeEvent(self, event): event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())