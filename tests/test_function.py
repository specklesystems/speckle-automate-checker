"""Run integration tests with a speckle server."""

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function,
)
from speckle_automate.fixtures import *  # noqa: F401, F403

from inputs import MinimumSeverity
from src.function import automate_function
from src.helpers import speckle_print
from src.inputs import FunctionInputs


class TestFunction:
    """Test suite for the automate function."""

    def test_function_run(self, test_automation_run_data: AutomationRunData, test_automation_token: str):
        """Run an integration test for the automate function.

        Args:
            test_automation_run_data (AutomationRunData): The automation run data provided by sdk.
            test_automation_token (str): The automation token.

        """
        speckle_print(str(test_automation_run_data))
        speckle_print(str(test_automation_token))

        """Run an integration test for the automate function."""
        automation_context = AutomationContext.initialize(test_automation_run_data, test_automation_token)
        default_url: str = (
            "https://speckle-model-checker-cedxvz7lzq-ew.a.run.app/r/6hdycwPELyTIT7Ueedh0UsWdJlTBefwSjDlcnd8LXGg/tsv"
        )

        automate_sdk = run_function(
            automation_context,
            automate_function,
            FunctionInputs(spreadsheet_url=default_url, minimum_severity=MinimumSeverity.INFO, hide_skipped=True),
        )

        assert automate_sdk.run_status == AutomationStatus.SUCCEEDED
