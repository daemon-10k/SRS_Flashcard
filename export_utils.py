# App/export_utils.py
import json

def export_deck_to_json(deck_data: dict, file_path: str) -> bool:
    """
    Exports a deck and its cards to a JSON file.

    Args:
        deck_data: A dictionary containing 'deck_name' and a list of 'cards'.
        file_path: The full path to save the JSON file to.

    Returns:
        True if the export is successful, False otherwise.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            # Use indent=2 for a human-readable file format
            json.dump(deck_data, f, ensure_ascii=False, indent=2)
        return True
    except (IOError, TypeError) as e:
        print(f"Error exporting deck to JSON: {e}")
        return False