from typing import Any

import pytest

from src.rules import PropertyRules


class TestValueComparison:
    """Test suite for value comparison functionality."""

    @pytest.mark.parametrize(
        "value1, value2",
        [
            # Basic numeric strings
            ("1400", 1400.0),
            ("1400.0", 1400),
            ("1400.00", 1400),
            # Whitespace handling
            (" 1400 ", 1400.0),
            ("  1400  ", 1400.0),
            ("\t1400\n", 1400.0),
            # Negative numbers
            ("-1400", -1400.0),
            (" -1400 ", -1400.0),
            ("-1400.0", -1400),
            # Zero handling
            ("0", 0.0),
            ("-0", 0.0),
            ("0.0", 0),
            # Simple integers
            ("1", 1),
            ("1.0", 1),
        ],
    )
    def test_numeric_string_comparison(self, value1: Any, value2: Any):
        """Test comparison of numeric strings with numbers."""
        assert PropertyRules.compare_values(value1, value2)
        # Test reverse comparison
        assert PropertyRules.compare_values(value2, value1)

    @pytest.mark.parametrize(
        "value1, value2, expected",
        [
            ("Yes", True, True),
            ("No", False, True),
            ("yes", True, True),
            ("no", False, True),
            ("YES", True, True),
            ("NO", False, True),
            ("true", True, True),
            ("false", False, True),
            ("True", True, True),
            ("False", False, True),
        ],
    )
    def test_boolean_string_comparison(self, value1: str, value2: bool, expected: bool):
        """Test comparison of boolean strings with booleans."""
        assert PropertyRules.compare_values(value1, value2) == expected
        # Test reverse comparison
        assert PropertyRules.compare_values(value2, value1) == expected

    @pytest.mark.parametrize(
        "value1, value2, case_sensitive, expected",
        [
            ("hello", "HELLO", False, True),
            ("hello", "HELLO", True, False),
            ("Hello", "hello", False, True),
            ("Hello", "Hello", True, True),
        ],
    )
    def test_string_comparison(self, value1: str, value2: str, case_sensitive: bool, expected: bool):
        """Test string comparison with case sensitivity options."""
        assert PropertyRules.compare_values(value1, value2, case_sensitive=case_sensitive) == expected

    @pytest.mark.parametrize(
        "value1, value2, tolerance, expected",
        [
            (1.0001, 1.0, 1e-3, True),
            (1.0001, 1.0, 1e-6, False),
            (1.00000001, 1.0, 1e-6, True),
            (-1.0001, -1.0, 1e-3, True),
        ],
    )
    def test_float_comparison_tolerance(self, value1: float, value2: float, tolerance: float, expected: bool):
        """Test float comparison with different tolerance levels."""
        assert PropertyRules.compare_values(value1, value2, tolerance=tolerance) == expected
