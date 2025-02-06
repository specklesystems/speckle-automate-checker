"""Run integration tests with a speckle server."""

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function
)

from src.inputs import FunctionInputs
from src.function import automate_function


def test_function_run(test_automation_run_data: AutomationRunData, test_automation_token: str):
    """Run an integration test for the automate function."""
    automation_context = AutomationContext.initialize(
        test_automation_run_data, test_automation_token
    )
    default_url: str = (
        "https://docs.google.com/spreadsheets/d/e/2PACX-1vSFmjLfqxPKXJHg-wEs1cp_nJEJJhESGVTLCvWLG_"
        "IgIuRZ4CmMDCSceOYFvuo8IqcmT4sj9qPiLfCx/pub?gid=0&single=true&output=tsv"
    )

    automate_sdk = run_function(
        automation_context,
        automate_function,
        FunctionInputs(spreadsheet_url=default_url),
    )

    assert automate_sdk.run_status == AutomationStatus.SUCCEEDED

# cli command to run just this test with pytest: pytest tests/local_test_exercise2.py::test_function_run
