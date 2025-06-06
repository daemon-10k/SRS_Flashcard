# App/srs_logic.py
import math
from datetime import datetime, timedelta

def calculate_srs_update(quality: int, repetitions: int, ease_factor: float, interval: int):
    """
    Calculates new SRS parameters based on SM-2 algorithm principles.

    Args:
        quality (int): User's assessment of recall quality (0-5, where 5 is perfect recall).
        repetitions (int): Number of times the card has been successfully recalled in a row.
        ease_factor (float): The current ease factor for the card.
        interval (int): The current interval in days before the card is due again.

    Returns:
        tuple: (new_repetitions, new_ease_factor, new_interval_days)
    """
    if quality < 4:  # If recall quality is poor (e.g., < 3 on a 0-5 scale)
        new_repetitions = 0  # Reset repetitions
        new_interval_days = 1  # Show again tomorrow
    else:
        new_repetitions = repetitions + 1
        if new_repetitions == 1:
            new_interval_days = 1
        elif new_repetitions == 2:
            new_interval_days = 6
        else:
            # For interval > 2, interval = previous_interval * ease_factor
            new_interval_days = math.ceil(interval * ease_factor)
    
    # Update ease_factor
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3  # Minimum ease factor

    # Cap interval for practical purposes if desired, e.g., 365 days
    # new_interval_days = min(new_interval_days, 365)

    return new_repetitions, new_ease_factor, new_interval_days