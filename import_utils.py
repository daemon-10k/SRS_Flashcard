# App/import_utils.py
import json

def parse_json_deck_file(file_path: str):
    """
    Parses a JSON deck file and returns the deck name and cards data.

    Args:
        file_path: Path to the JSON file.

    Returns:
        A tuple (deck_name, cards_data) if successful.
        Raises FileNotFoundError, json.JSONDecodeError, or ValueError on parsing issues.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        raise # Re-raise the exception to be caught by the caller
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        raise # Re-raise
    except Exception as e:
        print(f"An unexpected error occurred reading file {file_path}: {e}")
        raise

    deck_name = data.get("deck_name")
    cards_data = data.get("cards", [])

    if not deck_name or not isinstance(deck_name, str) or not deck_name.strip():
        raise ValueError("Import Error: JSON file must contain a valid 'deck_name'.")
    if not isinstance(cards_data, list):
        raise ValueError("Import Error: JSON file must contain a list of 'cards'.")
        
    # Basic validation for card structure
    for card_item in cards_data:
        if not isinstance(card_item, dict) or "front" not in card_item or "back" not in card_item:
            print(f"Warning: Skipping invalid card data during parsing: {card_item}")
            # Decide on stricter error handling: raise ValueError or filter out invalid cards
    
    # Filter out potentially invalid cards before returning if you want to be lenient
    # valid_cards_data = [card for card in cards_data if isinstance(card, dict) and "front" in card and "back" in card]

    return deck_name.strip(), cards_data # Or valid_cards_data