"""This module contains the function's business logic.

Use the automation_context module to wrap your function in an Automate context helper.
"""

from speckle_automate import AutomationContext, AutomateBase

from src.rules import apply_rules_to_objects
from src.inputs import FunctionInputs
from src.helpers import flatten_base
from src.spreadsheet import read_rules_from_spreadsheet


def automate_function(
        automate_context: AutomationContext,
        function_inputs: FunctionInputs,
) -> None:
    """This version of the function will add a check for the new provide inputs.

    Args:
        automate_context: A context helper object, that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data, that triggered this run.
            It also has convenience methods attach result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """

    # the context provides a convenient way, to receive the triggering version
    version_root_object = automate_context.receive_version()

    # We can continue to work with a flattened list of objects.
    flat_list_of_objects = list(flatten_base(version_root_object))

    # read the rules from the spreadsheet
    rules = read_rules_from_spreadsheet(function_inputs.spreadsheet_url)

    # apply the rules to the objects
    apply_rules_to_objects(flat_list_of_objects, rules, automate_context)

    # set the automation context view, to the original model / version view
    automate_context.set_context_view()

    # report success
    automate_context.mark_run_success(
        f"Successfully applied rules to {len(flat_list_of_objects)} objects."
    )
