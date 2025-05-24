# App/page_handlers/card_display_ui.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
import deck_manager

def create_card_widget(card_data: dict, edit_callback, delete_callback) -> QWidget:
    """
    Creates a widget to display a single card with Edit and Delete buttons.
    card_data is a dict like {"id": ..., "front": ..., "back": ...}
    """
    card_widget = QFrame()
    card_widget.setFrameShape(QFrame.Shape.StyledPanel)
    # card_widget.setFrameShadow(QFrame.Shadow.Raised) # Optional shadow

    main_layout = QVBoxLayout(card_widget)

    front_label = QLabel(f"<b>Front:</b> {card_data.get('front', 'N/A')}")
    front_label.setWordWrap(True)
    back_label = QLabel(f"<b>Back:</b> {card_data.get('back', 'N/A')}")
    back_label.setWordWrap(True)

    main_layout.addWidget(front_label)
    main_layout.addWidget(back_label)

    # Buttons layout
    buttons_layout = QHBoxLayout()
    edit_button = QPushButton("Edit")
    delete_button = QPushButton("Delete")

    # Store card_id with buttons if needed, or pass card_data directly to callbacks
    card_id = card_data.get("id")
    edit_button.clicked.connect(lambda checked=False, c_id=card_id, c_front=card_data.get('front'), c_back=card_data.get('back'): edit_callback(c_id, c_front, c_back))
    delete_button.clicked.connect(lambda checked=False, c_id=card_id: delete_callback(c_id))

    buttons_layout.addStretch() # Push buttons to the right
    buttons_layout.addWidget(edit_button)
    buttons_layout.addWidget(delete_button)
    
    main_layout.addLayout(buttons_layout)
    card_widget.setStyleSheet("QFrame {border: 1px solid #cccccc; border-radius: 5px; margin-bottom: 5px; padding: 5px;}")
    return card_widget

def populate_card_list(
    card_list_layout: QVBoxLayout, 
    deck_id: int,
    edit_card_callback, # To be connected to MainWindow's edit handler
    delete_card_callback # To be connected to MainWindow's delete handler
):
    """
    Clears and populates the card list layout for the given deck_id.
    """
    while card_list_layout.count():
        child = card_list_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
            
    cards = deck_manager.get_cards_for_deck(deck_id)
    if cards:
        for card_data in cards:
            widget = create_card_widget(card_data, edit_card_callback, delete_card_callback)
            card_list_layout.addWidget(widget)
    else:
        no_cards_label = QLabel("This deck has no cards yet. Click 'Add New Card' to create some!")
        no_cards_label.setStyleSheet("font-style: italic;")
        card_list_layout.addWidget(no_cards_label)