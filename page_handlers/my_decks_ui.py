# App/page_handlers/my_decks_ui.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget # Ensure QStackedWidget is imported if type hinting needs it

# Correctly import deck_manager from the parent App directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import deck_manager

def create_deck_widget(deck_id: int, deck_name: str, open_deck_callback) -> QWidget:
    """
    Creates a widget to display a single deck with an open button.
    """
    card_widget = QWidget()
    card_layout = QVBoxLayout(card_widget)

    label = QLabel(deck_name) # This will now receive the correct deck name string
    label.setStyleSheet("font-weight: bold; font-size: 16px;")

    open_button = QPushButton("Open Deck")
    open_button.clicked.connect(lambda checked=False, d_id=deck_id, d_name=deck_name: open_deck_callback(d_id, d_name))

    card_layout.addWidget(label)
    card_layout.addWidget(open_button)
    card_widget.setStyleSheet("border: 1px solid gray; border-radius: 8px; padding: 8px; margin-bottom: 5px;")
    return card_widget

def populate_decks_list(
    deck_list_layout: QVBoxLayout, 
    list_stacked_widget: QStackedWidget, # Explicitly type hint QStackedWidget
    list_page_widget: QWidget,    
    no_decks_page_widget: QWidget, 
    open_deck_callback 
):
    """
    Clears and re-populates the list of decks in the provided layout.
    """
    while deck_list_layout.count():
        child = deck_list_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    
    decks_data = deck_manager.get_all_decks() # Fetches list of dicts e.g. [{'id': 1, 'name': 'Test Deck'}]

    if decks_data:
        if list_stacked_widget and list_page_widget:
            list_stacked_widget.setCurrentWidget(list_page_widget)
        
        # CORRECTED LOOP:
        for deck_item in decks_data: # Iterate through the list of dictionaries
            deck_id = deck_item["id"]       # Get 'id' value from the dictionary
            deck_name = deck_item["name"]   # Get 'name' value from the dictionary
            deck_widget_item = create_deck_widget(deck_id, deck_name, open_deck_callback)
            deck_list_layout.addWidget(deck_widget_item)
    else:
        if list_stacked_widget and no_decks_page_widget:
            list_stacked_widget.setCurrentWidget(no_decks_page_widget)
        else: 
            no_decks_label = QLabel("No decks found. Import or create a new deck.")
            deck_list_layout.addWidget(no_decks_label)