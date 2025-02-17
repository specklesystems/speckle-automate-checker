import pandas as pd
import pytest

from src.rule_processor import SeverityLevel, get_severity


@pytest.mark.parametrize(
    "input_severity, expected_enum",
    [
        ("INFO", SeverityLevel.INFO),
        ("info", SeverityLevel.INFO),
        ("Info", SeverityLevel.INFO),
        ("WARNING", SeverityLevel.WARNING),
        ("warning", SeverityLevel.WARNING),
        ("Warning", SeverityLevel.WARNING),
        ("ERROR", SeverityLevel.ERROR),
        ("error", SeverityLevel.ERROR),
        ("Error", SeverityLevel.ERROR),
        ("WARN", SeverityLevel.WARNING),  # Invalid → Defaults to ERROR
        ("warn", SeverityLevel.WARNING),  # Invalid → Defaults to ERROR
        ("Critical", SeverityLevel.ERROR),  # Invalid → Defaults to ERROR
        ("Severe", SeverityLevel.ERROR),  # Invalid → Defaults to ERROR
        ("", SeverityLevel.ERROR),  # Empty string → Defaults to ERROR
        (None, SeverityLevel.ERROR),  # None → Defaults to ERROR
        (1.0, SeverityLevel.ERROR),  # None → Defaults to ERROR
    ],
)
def test_severity_conversion(input_severity, expected_enum):
    """Test various user inputs for severity and check expected outputs."""
    rule_info = pd.Series({"Report Severity": input_severity})
    severity = get_severity(rule_info)

    assert severity == expected_enum, f"Failed for input: {input_severity}"
