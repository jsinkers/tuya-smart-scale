"""Utility functions for the Tuya Smart Scale integration."""

from datetime import datetime, date
import logging

_LOGGER = logging.getLogger(__name__)


def calculate_age_from_birthdate(birthdate_str: str) -> int:
    """Calculate current age from birthdate string in YYYY-MM-DD format.
    
    Args:
        birthdate_str: Birthdate string in YYYY-MM-DD format
        
    Returns:
        Current age in years, or 30 as default if invalid birthdate
    """
    try:
        birth_date = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except (ValueError, TypeError):
        _LOGGER.warning(f"Invalid birthdate format: {birthdate_str}, using default age 30")
        return 30  # Default age if invalid birthdate
