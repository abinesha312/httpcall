"""Phone number validation and security checks."""

import re
from typing import Tuple


def validate_e164(phone_number: str) -> Tuple[bool, str]:
    """
    Validate that a phone number is in E.164 format.
    
    E.164 format: +[country code][subscriber number]
    Maximum 15 digits including country code.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not phone_number:
        return False, "Phone number is required"
    
    if not isinstance(phone_number, str):
        return False, "Phone number must be a string"
    
    phone_number = phone_number.strip()
    
    if not phone_number.startswith("+"):
        return False, "Phone number must start with '+' (E.164 format)"
    
    digits_only = phone_number[1:]
    
    if not digits_only.isdigit():
        return False, "Phone number must contain only digits after '+'"
    
    if len(digits_only) < 7:
        return False, "Phone number too short (minimum 7 digits)"
    
    if len(digits_only) > 15:
        return False, "Phone number too long (maximum 15 digits)"
    
    if is_likely_premium_rate(phone_number):
        return False, "Premium rate numbers are not allowed"
    
    return True, ""


def is_likely_premium_rate(phone_number: str) -> bool:
    """
    Check if a phone number looks like a premium rate number.
    
    This is a basic check for common premium rate patterns:
    - US: +1900*, +1976*
    - UK: +44[789]* (simplified check for 09*)
    - International premium: +979* (reserved for premium services)
    
    Args:
        phone_number: Phone number in E.164 format
        
    Returns:
        True if the number appears to be premium rate
    """
    premium_patterns = [
        r"^\+1900",      # US premium
        r"^\+1976",      # US premium
        r"^\+4409",      # UK premium (simplified)
        r"^\+979",       # International premium
    ]
    
    for pattern in premium_patterns:
        if re.match(pattern, phone_number):
            return True
    
    return False
