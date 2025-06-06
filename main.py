# App/main.py
import sys
import os
import sqlite3
from PyQt6.QtWidgets import (QApplication, QWidget, QMessageBox, QVBoxLayout, # type: ignore
                             QPushButton, QLabel, QFormLayout, QTextEdit, QDialogButtonBox, QDialog)
from PyQt6.uic import loadUi # type: ignore

# Modular imports
import deck_manager
from page_handlers import my_decks_ui, card_display_ui
from handlers import auth_handler, deck_handler, card_handler, review_handler

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(APP_DIR, "database")
UI_FILE_PATH = os.path.join(APP_DIR, "main.ui")

SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)"""

class EditCardDialog(QDialog):
    def __init__(self, current_front, current_back, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Card")
        self.setMinimumWidth(300)
        self.layout = QFormLayout(self)
        self.front_text_edit = QTextEdit(current_front)
        self.back_text_edit = QTextEdit(current_back)
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
        self.APP_DIR = APP_DIR
        os.makedirs(DATABASE_DIR, exist_ok=True)
        if not os.path.exists(UI_FILE_PATH):
            QMessageBox.critical(None, "Error", f"UI file not found: {UI_FILE_PATH}")
            sys.exit(1)
        loadUi(UI_FILE_PATH, self)
        
        user_deck_db_path = None

        self.page_history = []
        self._navigating_back = False
        self.current_deck_id = None
        self.current_deck_name = None
        self.current_review_deck_id = None
        self.review_cards_list = []
        self.current_review_card_index = -1
        self.current_review_card_data = None
        self.showing_answer = False

        self._connect_signals()
        self._init_user_database()
        
        self.main_stackedWidget.setCurrentWidget(self.login_page)
        self._update_all_back_button_states()

    def _connect_signals(self):
        # Auth
        self.login_goToRegister_button.clicked.connect(self.show_register_page)
        self.login_submit_button.clicked.connect(lambda: auth_handler.handle_login(self))
        self.register_submit_button.clicked.connect(lambda: auth_handler.handle_registration(self))

        # Navigation
        if hasattr(self, 'register_goBackButton'): self.register_goBackButton.clicked.connect(self.handle_go_back)
        if hasattr(self, 'review_goBackButton'): self.review_goBackButton.clicked.connect(self.handle_go_back)
        if hasattr(self, 'myDecks_goBackButton'): self.myDecks_goBackButton.clicked.connect(self.handle_go_back)
        if hasattr(self, 'card_list_goBackButton'): self.card_list_goBackButton.clicked.connect(self.handle_go_back_to_my_decks)
        if hasattr(self, 'statistics_goBackButton'): self.statistics_goBackButton.clicked.connect(self.handle_go_back)

        # Dashboard
        self.dashboard_goToMyDecks_button.clicked.connect(self.show_myDecks_page)
        self.dashboard_goToReview_button.clicked.connect(lambda: review_handler.start_review_session(self))
        self.dashboard_goToStatistics_button.clicked.connect(self.show_statistics_page)
        self.dashboard_logout_button.clicked.connect(self.show_login_page) 

        # Deck Management
        if hasattr(self, 'myDecks_noDecks_create_button'): self.myDecks_noDecks_create_button.clicked.connect(lambda: deck_handler.handle_create_new_deck(self))
        if hasattr(self, 'myDecks_noDecks_import_button'): self.myDecks_noDecks_import_button.clicked.connect(lambda: deck_handler.handle_import_deck(self))
        if hasattr(self, 'myDecks_list_create_button'): self.myDecks_list_create_button.clicked.connect(lambda: deck_handler.handle_create_new_deck(self))
        if hasattr(self, 'myDecks_list_import_button'): self.myDecks_list_import_button.clicked.connect(lambda: deck_handler.handle_import_deck(self))

        # Card Management
        if hasattr(self, 'card_list_add_card_button'): self.card_list_add_card_button.clicked.connect(lambda: card_handler.handle_add_new_card(self))
        if hasattr(self, 'card_list_export_deck_button'): self.card_list_export_deck_button.clicked.connect(lambda: deck_handler.handle_export_deck(self))

        # Review
        if hasattr(self, 'review_showAnswer_button'): self.review_showAnswer_button.clicked.connect(lambda: review_handler.handle_show_answer(self))
        if hasattr(self, 'review_easy_button'): self.review_easy_button.clicked.connect(lambda: review_handler.handle_difficulty_selected(self, 5))
        if hasattr(self, 'review_medium_button'): self.review_medium_button.clicked.connect(lambda: review_handler.handle_difficulty_selected(self, 4))
        if hasattr(self, 'review_hard_button'): self.review_hard_button.clicked.connect(lambda: review_handler.handle_difficulty_selected(self, 3))

    def _init_user_database(self):
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

    def _navigate_to_page(self, target_page_widget):
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
            if previous_widget == self.dashboard_page: self.current_review_deck_id = None
            self._navigating_back = False
            self._update_all_back_button_states()
        else:
            self._update_all_back_button_states()

    def handle_go_back_to_my_decks(self):
        self._navigating_back = True
        self.current_review_deck_id = None
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

    def _update_back_button_state(self, button_widget):
        if button_widget: button_widget.setEnabled(bool(self.page_history))

    def show_register_page(self): self._navigate_to_page(self.register_page)
    def show_login_page(self): self.page_history.clear(); self._navigate_to_page(self.login_page)
    def show_dashboard_page(self): self.current_review_deck_id = None; self.page_history.clear(); self._navigate_to_page(self.dashboard_page)
    def show_myDecks_page(self): self._display_my_decks_list_content(); self._navigate_to_page(self.myDecks_page)
    def show_statistics_page(self): self.get_statistics(); self._navigate_to_page(self.statistics_page)
    
    def show_card_list_page(self):
        if self.current_deck_id is None:
            QMessageBox.warning(self, "Error", "No deck selected."); self.show_myDecks_page(); return
        if hasattr(self, 'card_list_deck_name_label'):
            self.card_list_deck_name_label.setText(f"Deck: {self.current_deck_name}")
        self._display_deck_cards_content()
        self._navigate_to_page(self.card_list_page)

    def _display_my_decks_list_content(self):
        if not all(hasattr(self, name) for name in ['myDecks_list_verticalLayout', 'myDecks_list_stackedWidget', 'myDecks_list_page', 'myDecks_noDecks_page']):
            QMessageBox.warning(self, "UI Error", "MyDecks page UI elements not fully loaded."); return
        my_decks_ui.populate_decks_list(
            deck_list_layout=self.myDecks_list_verticalLayout,
            list_stacked_widget=self.myDecks_list_stackedWidget,
            list_page_widget=self.myDecks_list_page, no_decks_page_widget=self.myDecks_noDecks_page,
            open_deck_callback=self.handle_open_deck,
            user_deck_db_path=self.user_deck_db_path
        )

    def handle_open_deck(self, deck_id, deck_name):
        self.current_deck_id = deck_id
        self.current_deck_name = deck_name
        self.current_review_deck_id = deck_id
        self.show_card_list_page()

    def _display_deck_cards_content(self):
        if self.current_deck_id is None: return
        if not hasattr(self, 'card_list_verticalLayout'):
             QMessageBox.warning(self, "UI Error", "Card list UI elements not loaded."); return
        card_display_ui.populate_card_list(
            card_list_layout=self.card_list_verticalLayout,
            deck_id=self.current_deck_id,
            edit_card_callback=lambda id, f, b: card_handler.handle_edit_card(self, id, f, b),
            delete_card_callback=lambda id: card_handler.handle_delete_card(self, id),
            user_deck_db_path=self.user_deck_db_path # Pass the user's deck database path
        )
        
    def get_statistics(self):
        """
        Fetches global statistics and displays them on the statistics page.
        """
        if not self.user_deck_db_path:
            QMessageBox.critical(self, "Error", "No user is currently logged in.")
            return

        # Fetch the statistics from the deck manager
        stats = deck_manager.get_global_statistics(self.user_deck_db_path)
        print(f"Fetched statistics: {stats}")

        # Update the labels on the statistics page with the new data
        if hasattr(self, 'stats_totalDecks_label'):
            self.stats_totalDecks_label.setText(f"Total Decks: {stats['total_decks']}")
        
        if hasattr(self, 'stats_totalCards_label'):
            self.stats_totalCards_label.setText(f"Total Cards: {stats['total_cards']}")
            
        if hasattr(self, 'stats_finishedCards_label'):
            self.stats_finishedCards_label.setText(f"Learned Cards: {stats['finished_cards']}")

        if hasattr(self, 'stats_dueToday_label'):
            self.stats_dueToday_label.setText(f"Cards Due Today: {stats['due_today']}")

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())