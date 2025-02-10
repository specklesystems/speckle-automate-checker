from enum import Enum

from pydantic import Field
from speckle_automate import AutomateBase


class PropertyMatchMode(Enum):
    STRICT = "strict" # Exact parameter path match
    FUZZY = "fuzzy"   # Search all parameters ignoring hierarchy
    MIXED = "mixed"   # Exact match first, fuzzy fallback

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

    property_match_mode: PropertyMatchMode = Field(
        default=PropertyMatchMode.MIXED,
        title="Property Match Mode",
        description='Controls how strictly parameter names must match. ' +
                    'STRICT will only match exact parameter paths, ' +
                    'FUZZY will search all parameters ignoring hierarchy, ' +
                    'MIXED will exact match first, fuzzy fallback.'
    )
