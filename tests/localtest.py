"""Run integration tests with a speckle server."""
from speckle_automate.fixtures import *

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function,
)

from src.function import automate_function
from src.helpers import speckle_print
from src.inputs import FunctionInputs

def test_function_run(test_automation_run_data: AutomationRunData, test_automation_token: str):

    speckle_print(str(test_automation_run_data))
    speckle_print(str(test_automation_token))

    """Run an integration test for the automate function."""
    automation_context = AutomationContext.initialize(
        test_automation_run_data, test_automation_token
    )
    default_url: str = (
        "https://drive.google.com/uc?export=download&id=1hiPSw23eOaqd27QD_YsXvZg9PWm7_XBx"
    )

    automate_sdk = run_function(
        automation_context,
        automate_function,
        FunctionInputs(spreadsheet_url=default_url),
    )

    assert automate_sdk.run_status == AutomationStatus.SUCCEEDED