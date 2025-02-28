"""This is the main entry point for the Speckle Automate function.

The Speckle Automate system works as follows:
1. When a model is committed to Speckle, it triggers automations associated with the project
2. For each automation, Speckle Automate prepares a runtime environment and context
3. The automation context includes the model data and function inputs
4. This function is executed to process the model and provide results
5. Results are attached to objects in the model, creating an annotated view

This function implements a configurable rule-based validation system that:
- Reads validation rules from an external spreadsheet
- Applies these rules to objects in the Speckle model
- Reports validation results back to the Speckle platform
- Provides an annotated view of the model showing validation issues
"""

from speckle_automate import AutomationContext
from specklepy.objects.base import Base

from src.helpers import flatten_base, speckle_print
from src.inputs import FunctionInputs
from src.rule_processor import apply_rules_to_objects
from src.spreadsheet import read_rules_from_spreadsheet

VERSION: int = 2


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """Main entry point for the Speckle Automate function.

    This function is called by the Speckle Automate system when the automation is triggered.
    It orchestrates the entire validation process:

    1. Receiving and flattening the model data
    2. Detecting the Speckle object schema version
    3. Loading and grouping rules from the external spreadsheet
    4. Applying rules to objects and collecting results
    5. Reporting results back to the Speckle platform

    Args:
        automate_context: A context helper provided by Speckle Automate that:
            - Provides access to the Speckle model data
            - Handles result reporting and view management
            - Manages run status (success, failure, exception)
        function_inputs: User-provided inputs defined in the FunctionInputs schema,
            particularly the URL to the rules spreadsheet
    """
    # -------------------------------------------------------------------------
    # Step 1: Receive and process the model data
    # -------------------------------------------------------------------------

    # The AutomationContext provides a convenient way to access the model data
    # that triggered this automation run
    version_root_object: Base = automate_context.receive_version()

    # Flatten the object tree into a list of objects
    # The Speckle object model is hierarchical, but for validation purposes,
    # it's easier to work with a flat list of objects
    flat_list_of_objects = list(flatten_base(version_root_object))

    # -------------------------------------------------------------------------
    # Step 2: Detect Speckle object schema version
    # -------------------------------------------------------------------------

    # The Speckle object schema has evolved over time
    # In newer models, we can detect the version from the root object
    # This version information helps our validation logic handle different schemas
    global VERSION
    VERSION = getattr(version_root_object, "version", 2)  # noqa: F841SION = getattr(version_root_object,"version", 2)  # noqa: F841  # noqa: F841

    # In v2, parameters are stored in a 'parameters' dictionary on each object
    # In v3, they are nested in 'properties.Parameters' with categorization
    speckle_print(f"Detected Speckle object schema version: {VERSION}")

    # -------------------------------------------------------------------------
    # Step 3: Load and process rules from the spreadsheet
    # -------------------------------------------------------------------------

    # The rules are defined in an external spreadsheet (TSV format)
    # This allows non-technical users to define and modify rules
    # without changing the code
    grouped_rules, messages = read_rules_from_spreadsheet(function_inputs.spreadsheet_url)

    # Handle any validation messages from rule processing
    for message in messages:
        speckle_print(message)  # or log them appropriately

    # If rule processing failed, mark the run as failed and exit
    if grouped_rules is None:
        automate_context.mark_run_exception("Failed to process rules")
        return

    # -------------------------------------------------------------------------
    # Step 4: Apply rules to objects and collect results
    # -------------------------------------------------------------------------

    # This is where the actual validation happens
    # Each rule is applied to relevant objects, and results are collected
    # Results are attached to objects in the model to create an annotated view
    apply_rules_to_objects(
        flat_list_of_objects,
        grouped_rules,
        automate_context,
        minimum_severity=function_inputs.minimum_severity,
        hide_skipped=function_inputs.hide_skipped,
    )

    # -------------------------------------------------------------------------
    # Step 5: Finalize the automation run
    # -------------------------------------------------------------------------

    # Set the context view to the original model/version view
    # This ensures that the results are displayed in the correct context
    automate_context.set_context_view()

    # Mark the run as successful and provide a summary message
    # This message will be displayed to the user in the Speckle UI
    automate_context.mark_run_success(
        f"Successfully applied {len(grouped_rules)} rules to {len(flat_list_of_objects)} version {VERSION} objects."
    )
