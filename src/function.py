# This is the main function that will be executed when the automation is triggered.
# It will receive the inputs from the user, and the context of the run.
# It will then apply the rules to the objects in the model, and report back the results.


from pandas import DataFrame
from speckle_automate import AutomationContext

from src.helpers import flatten_base
from src.inputs import FunctionInputs
from src.rule_processor import apply_rules_to_objects
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

    # If it is a next_gen model, we can get the version from the root object
    if type(version_root_object) == "Base":
        version = version_root_object.version
    else:
        version = None

    # read the rules from the spreadsheet
    rules: DataFrame = read_rules_from_spreadsheet(function_inputs.spreadsheet_url)

    if (rules is None) or (len(rules) == 0):
        automate_context.mark_run_exception("No rules defined")

    grouped_rules = rules.groupby("Rule Number")

    # apply the rules to the objects
    apply_rules_to_objects(flat_list_of_objects, grouped_rules, automate_context)

    # set the automation context view, to the original model / version view
    automate_context.set_context_view()

    # report success
    automate_context.mark_run_success(
        f"Successfully applied {len(grouped_rules)} rules to {len(flat_list_of_objects)} objects."
    )
