from enum import Enum

from pydantic import Field
from speckle_automate import AutomateBase


class PropertyMatchMode(Enum):
    STRICT = "strict" # Exact parameter path match
    FUZZY = "fuzzy"   # Search all parameters ignoring hierarchy
    MIXED = "mixed"   # Exact match first, fuzzy fallback

class MinimumSeverity(str, Enum):
    """Enum for minimum severity level to report."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """







    # In this exercise, we will move rules to an external source so not to hardcode them.
    spreadsheet_url: str = Field(
        title="Spreadsheet URL",
        description="This is the URL of the spreadsheet to check. It should be a TSV format data source.",
    )

    minimum_severity: MinimumSeverity = Field(
        default=MinimumSeverity.INFO,
        title="Minimum Severity Level",
        description="Only report test results with this severity level or higher. Info will show all results, Warning will show warnings and errors, Error will show only errors.",
    )

    hide_skipped: bool = Field(
        default=False,
        title="Hide Skipped Tests",
        description="If enabled, tests that were skipped (no matching objects found) will not be reported.",
    )
