# App/page_handlers/my_decks_ui.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget, QProgressBar # type: ignore
import deck_manager

def create_deck_widget(deck_id: int, deck_name: str, stats: dict, open_deck_callback) -> QWidget:
    """
    Creates a widget to display a single deck with an open button.
    """
    card_widget = QWidget()
    card_layout = QVBoxLayout(card_widget)

    label = QLabel(deck_name)
    label.setStyleSheet("font-weight: bold; font-size: 16px;")
    
    total_cards = stats.get('total_cards', 0)
    finished_cards = stats.get('finished_cards', 0)

    stats_label = QLabel(f"Progress: {finished_cards} / {total_cards} cards learned")
    stats_label.setStyleSheet("font-size: 12px;")

    progress_bar = QProgressBar()
    if total_cards > 0:
        progress_percentage = int((finished_cards / total_cards) * 100)
        progress_bar.setValue(progress_percentage)
    else:
        progress_bar.setValue(0)

    open_button = QPushButton("Open Deck")
    open_button.clicked.connect(lambda checked=False, d_id=deck_id, d_name=deck_name: open_deck_callback(d_id, d_name))

    card_layout.addWidget(label)
    card_layout.addWidget(stats_label)
    card_layout.addWidget(open_button)
    card_widget.setStyleSheet("border: 1px solid gray; border-radius: 8px; padding: 8px; margin-bottom: 5px;")
    return card_widget

def populate_decks_list(
    deck_list_layout: QVBoxLayout, 
    list_stacked_widget: QStackedWidget,
    list_page_widget: QWidget,    
    no_decks_page_widget: QWidget, 
    open_deck_callback,
    user_deck_db_path: str  # Pass the user's deck database path
):
    """
    Clears and re-populates the list of decks in the provided layout.
    """
    while deck_list_layout.count():
        child = deck_list_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    decks_data = deck_manager.get_all_decks(user_deck_db_path)  # Fetch decks from the user's database

    if decks_data:
        if list_stacked_widget and list_page_widget:
            list_stacked_widget.setCurrentWidget(list_page_widget)
        
        for deck_item in decks_data:
            deck_id = deck_item["id"]
            deck_name = deck_item["name"]
            
            deck_stats = deck_manager.get_deck_statistics(user_deck_db_path, deck_id)
            
            deck_widget_item = create_deck_widget(deck_id, deck_name, deck_stats, open_deck_callback)
            deck_list_layout.addWidget(deck_widget_item)
    else:
        if list_stacked_widget and no_decks_page_widget:
            list_stacked_widget.setCurrentWidget(no_decks_page_widget)
        else: 
            no_decks_label = QLabel("No decks found. Import or create a new deck.")
            deck_list_layout.addWidget(no_decks_label)