# App/handlers/review_handler.py
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QMessageBox, QInputDialog # type: ignore
import deck_manager
from utils import srs_logic

def start_review_session(main_window):
    """Initiates a review session."""
    if main_window.current_review_deck_id is None:
        decks = deck_manager.get_all_decks(main_window.user_deck_db_path)
        if not decks:
            QMessageBox.information(main_window, "Review", "No decks available to review.")
            main_window.show_dashboard_page()
            return
        deck_names = [d["name"] for d in decks]
        deck_name, ok = QInputDialog.getItem(main_window, "Select Deck", "Choose a deck to review:", deck_names, 0, False)
        if ok and deck_name:
            selected_deck_data = next((d for d in decks if d["name"] == deck_name), None)
            if selected_deck_data:
                main_window.current_review_deck_id = selected_deck_data["id"]
        else:
            main_window.show_dashboard_page()
            return

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    main_window.review_cards_list = deck_manager.get_due_cards(main_window.user_deck_db_path, main_window.current_review_deck_id, today_str)
    
    if not main_window.review_cards_list:
        QMessageBox.information(main_window, "Review Complete", "No cards due for review in this deck right now!")
        main_window.show_dashboard_page()
        return

    main_window.current_review_card_index = 0
    main_window.showing_answer = False
    load_review_card(main_window)
    main_window._navigate_to_page(main_window.review_page)

def load_review_card(main_window):
    """Loads the current card onto the review page UI."""
    if main_window.current_review_card_index < 0 or main_window.current_review_card_index >= len(main_window.review_cards_list):
        QMessageBox.information(main_window, "Review Complete", "You've reviewed all due cards in this session!")
        main_window.current_review_deck_id = None
        main_window.review_cards_list = []
        main_window.current_review_card_index = -1
        main_window.show_dashboard_page()
        return

    main_window.current_review_card_data = main_window.review_cards_list[main_window.current_review_card_index]
    
    if hasattr(main_window, 'review_cardDisplay_label'):
        if main_window.showing_answer:
            display_text = f"<b>Front:</b> {main_window.current_review_card_data['front']}\n\n<b>Back:</b> {main_window.current_review_card_data['back']}"
        else:
            display_text = f"<b>Front:</b> {main_window.current_review_card_data['front']}"
        main_window.review_cardDisplay_label.setText(display_text)
    
    if hasattr(main_window, 'review_showAnswer_button'):
        main_window.review_showAnswer_button.setVisible(not main_window.showing_answer)
    
    difficulty_buttons_visible = main_window.showing_answer
    if hasattr(main_window, 'review_easy_button'): main_window.review_easy_button.setVisible(difficulty_buttons_visible)
    if hasattr(main_window, 'review_medium_button'): main_window.review_medium_button.setVisible(difficulty_buttons_visible)
    if hasattr(main_window, 'review_hard_button'): main_window.review_hard_button.setVisible(difficulty_buttons_visible)
    
    if hasattr(main_window, 'review_title_label'):
        main_window.review_title_label.setText(f"Reviewing Deck (Card {main_window.current_review_card_index + 1}/{len(main_window.review_cards_list)})")

def handle_show_answer(main_window):
    """Shows the answer for the current review card."""
    main_window.showing_answer = True
    load_review_card(main_window)

def handle_difficulty_selected(main_window, quality: int):
    """Handles the selection of a difficulty level for a card."""
    if not main_window.current_review_card_data:
        return

    card = main_window.current_review_card_data
    reps = card.get('repetitions', 0)
    ef = card.get('ease_factor', 2.5)
    interval = card.get('interval', 1)

    new_reps, new_ef, new_interval_days = srs_logic.calculate_srs_update(quality, reps, ef, interval)
    
    new_due_date = datetime.now() + timedelta(days=new_interval_days)
    new_due_date_str = new_due_date.strftime("%Y-%m-%d %H:%M:%S")

    try:
        deck_manager.update_card_srs_details(main_window.user_deck_db_path, card['id'], new_due_date_str, new_interval_days, new_ef, new_reps)
    except Exception as e:
        QMessageBox.critical(main_window, "Database Error", f"Could not update card SRS details: {e}")
        
    main_window.current_review_card_index += 1
    main_window.showing_answer = False
    load_review_card(main_window)