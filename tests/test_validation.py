"""Tests for phone number validation."""

import pytest
from httpcall.validation import validate_e164, is_likely_premium_rate


class TestValidateE164:
    """Tests for E.164 phone number validation."""
    
    def test_valid_us_number(self):
        """Test valid US phone number."""
        is_valid, error = validate_e164("+12025551234")
        assert is_valid is True
        assert error == ""
    
    def test_valid_uk_number(self):
        """Test valid UK phone number."""
        is_valid, error = validate_e164("+442071234567")
        assert is_valid is True
        assert error == ""
    
    def test_valid_short_number(self):
        """Test valid short international number (7 digits)."""
        is_valid, error = validate_e164("+1234567")
        assert is_valid is True
        assert error == ""
    
    def test_valid_long_number(self):
        """Test valid long international number (15 digits)."""
        is_valid, error = validate_e164("+123456789012345")
        assert is_valid is True
        assert error == ""
    
    def test_missing_plus_sign(self):
        """Test number without + prefix."""
        is_valid, error = validate_e164("12025551234")
        assert is_valid is False
        assert "must start with '+'" in error
    
    def test_empty_string(self):
        """Test empty string."""
        is_valid, error = validate_e164("")
        assert is_valid is False
        assert "required" in error
    
    def test_none_value(self):
        """Test None value."""
        is_valid, error = validate_e164(None)
        assert is_valid is False
        assert "required" in error
    
    def test_non_string_type(self):
        """Test non-string input."""
        is_valid, error = validate_e164(12025551234)
        assert is_valid is False
        assert "must be a string" in error
    
    def test_contains_letters(self):
        """Test number with letters."""
        is_valid, error = validate_e164("+1202555ABCD")
        assert is_valid is False
        assert "only digits" in error
    
    def test_contains_spaces(self):
        """Test number with spaces."""
        is_valid, error = validate_e164("+1 202 555 1234")
        assert is_valid is False
        assert "only digits" in error
    
    def test_contains_hyphens(self):
        """Test number with hyphens."""
        is_valid, error = validate_e164("+1-202-555-1234")
        assert is_valid is False
        assert "only digits" in error
    
    def test_too_short(self):
        """Test number that's too short (< 7 digits)."""
        is_valid, error = validate_e164("+123456")
        assert is_valid is False
        assert "too short" in error
    
    def test_too_long(self):
        """Test number that's too long (> 15 digits)."""
        is_valid, error = validate_e164("+1234567890123456")
        assert is_valid is False
        assert "too long" in error
    
    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed."""
        is_valid, error = validate_e164("  +12025551234  ")
        assert is_valid is True
        assert error == ""
    
    def test_premium_us_900_number(self):
        """Test US 900 premium number is rejected."""
        is_valid, error = validate_e164("+19005551234")
        assert is_valid is False
        assert "Premium rate" in error
    
    def test_premium_us_976_number(self):
        """Test US 976 premium number is rejected."""
        is_valid, error = validate_e164("+19765551234")
        assert is_valid is False
        assert "Premium rate" in error
    
    def test_premium_uk_09_number(self):
        """Test UK 09 premium number is rejected."""
        is_valid, error = validate_e164("+44091234567")
        assert is_valid is False
        assert "Premium rate" in error
    
    def test_premium_international_979(self):
        """Test international 979 premium number is rejected."""
        is_valid, error = validate_e164("+9791234567")
        assert is_valid is False
        assert "Premium rate" in error


class TestIsPremiumRate:
    """Tests for premium rate detection."""
    
    def test_us_900_premium(self):
        """Test US 900 number is detected as premium."""
        assert is_likely_premium_rate("+19005551234") is True
    
    def test_us_976_premium(self):
        """Test US 976 number is detected as premium."""
        assert is_likely_premium_rate("+19765551234") is True
    
    def test_uk_09_premium(self):
        """Test UK 09 number is detected as premium."""
        assert is_likely_premium_rate("+44091234567") is True
    
    def test_international_979_premium(self):
        """Test international 979 is detected as premium."""
        assert is_likely_premium_rate("+9791234567") is True
    
    def test_normal_us_number(self):
        """Test normal US number is not premium."""
        assert is_likely_premium_rate("+12025551234") is False
    
    def test_normal_uk_number(self):
        """Test normal UK number is not premium."""
        assert is_likely_premium_rate("+442071234567") is False
    
    def test_normal_international_number(self):
        """Test normal international number is not premium."""
        assert is_likely_premium_rate("+33612345678") is False
