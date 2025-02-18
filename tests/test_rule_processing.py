"""Tests for rule processing functionality."""

import pandas as pd
import pytest


@pytest.fixture
def explicit_check_rule():
    """Create a rule using explicit CHECK format."""
    return pd.DataFrame(
        {
            "Rule Number": [1, 1, 1],
            "Logic": ["WHERE", "AND", "CHECK"],
            "Property Name": ["category", "width", "material"],
            "Predicate": ["matches", "greater than", "matches"],
            "Value": ["Walls", "200", "Concrete"],
            "Message": ["Test message", "", ""],
            "Severity": ["Error", "", ""],
        }
    )


@pytest.fixture
def legacy_rule():
    """Create a rule using legacy format (last AND is implicit check)."""
    return pd.DataFrame(
        {
            "Rule Number": [1, 1, 1],
            "Logic": ["WHERE", "AND", "AND"],
            "Property Name": ["category", "width", "material"],
            "Predicate": ["matches", "greater than", "matches"],
            "Value": ["Walls", "200", "Concrete"],
            "Message": ["Test message", "", ""],
            "Severity": ["Error", "", ""],
        }
    )
