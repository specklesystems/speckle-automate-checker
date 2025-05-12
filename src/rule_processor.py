"""Module for processing rules against Speckle objects and updating the automate context with the results.

This module implements the core rule processing logic that:
1. Validates rule structure and logic
2. Evaluates rule conditions against Speckle objects
3. Separates filtering conditions and final check conditions
4. Processes rule groups and tracks results
5. Reports results back to the Speckle Automate context

The rule processing follows a "filter then validate" approach:
- Filter conditions (WHERE, AND) narrow down which objects to check
- The final check condition (CHECK or last AND) determines pass/fail
"""

import json
from enum import Enum
from typing import Any

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy
from speckle_automate import AutomationContext, ObjectResultLevel
from specklepy.objects.base import Base

from src.helpers import speckle_print
from src.inputs import MinimumSeverity
from src.predicates import PREDICATE_METHOD_MAP
from src.rules import PropertyRules


def validate_rule_structure(rule_group: pd.DataFrame) -> None:
    """Validates the structure and logic of a rule group.

    This ensures the rule follows the proper format:
    - First condition must be WHERE
    - Following conditions can be AND
    - Only one CHECK condition is allowed (and must be last)

    Args:
        rule_group: DataFrame containing the rule conditions

    Raises:
        ValueError: If rule structure is invalid
    """
    if rule_group.empty:
        return

    # Validate Logic column exists
    if "Logic" not in rule_group.columns:
        raise ValueError("Rule must have a 'Logic' column")

    # Get uppercase Logic values for case-insensitive comparison
    logic_values = rule_group["Logic"].str.upper()

    # Check if first condition is WHERE
    if logic_values.iloc[0] != "WHERE":
        raise ValueError(f"Rule {rule_group.iloc[0]['Rule Number']} must start with WHERE")

    # Count CHECK conditions
    check_count = sum(1 for value in logic_values if value == "CHECK")
    if check_count > 1:
        raise ValueError(f"Rule {rule_group.iloc[0]['Rule Number']} has multiple CHECK conditions")

    # If CHECK exists, ensure it's the last condition
    check_indices = logic_values[logic_values == "CHECK"].index
    if check_count == 1 and check_indices[0] != rule_group.index[-1]:
        raise ValueError(f"CHECK must be the last condition in rule {rule_group.iloc[0]['Rule Number']}")

    # Validate Logic values
    valid_values = {"WHERE", "AND", "CHECK"}
    invalid_values = set(logic_values.unique()) - valid_values
    if invalid_values:
        raise ValueError(f"Invalid Logic values found: {invalid_values}")


def evaluate_condition(
    speckle_object: Base, condition: pd.Series, rule_number: str | None = None, case_number: int | None = None
) -> bool:
    """Evaluates a single condition against a Speckle object.

    This function is the bridge between the rules defined in the spreadsheet
    and the property checking methods in PropertyRules. It:
    1. Extracts the property name, predicate, and value from the condition
    2. Maps the predicate to the corresponding method in PropertyRules
    3. Calls the method with the object, property name, and value

    Args:
        speckle_object: The Speckle object to evaluate against
        condition: A pandas Series containing the condition details
            - 'Property Name': The name of the property to check
            - 'Predicate': The comparison operation (like 'equals', 'greater than')
            - 'Value': The value to compare against
        rule_number: For tracking, the rule number being evaluated
        case_number: For tracking, the condition number within the rule

    Returns:
        True if the condition is met, False otherwise
    """
    property_name = condition.get("Property Name", condition.get("Property Path"))
    predicate_key = condition["Predicate"]
    value = condition["Value"]

    # Debugging info
    _ = rule_number
    _ = case_number

    # Look up the method name in the predicate map
    # This map connects spreadsheet predicates to PropertyRules methods
    if predicate_key in PREDICATE_METHOD_MAP:
        method_name = PREDICATE_METHOD_MAP[predicate_key]
        method = getattr(PropertyRules, method_name, None)

        if method:
            # Call the method with the object, property name, and value
            return method(speckle_object, property_name, value)

    return False


def get_filters_and_check(rule_group: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separates rule conditions into filtering conditions and the final check condition.

    This function handles two rule formats:
    1. Explicit format: WHERE + AND... + CHECK
    2. Legacy format: WHERE + AND... (last AND is implicitly the check)

    This separation enables the "filter then validate" approach.

    Args:
        rule_group: DataFrame containing rule conditions

    Returns:
        Tuple containing (filter_conditions, final_check_condition)
    """
    if rule_group.empty:
        return pd.DataFrame(), pd.Series()

    # Get uppercase Logic values for case-insensitive comparison
    logic_values = rule_group["Logic"].str.upper()

    # Look for explicit CHECK
    check_conditions = rule_group[logic_values == "CHECK"]
    has_explicit_check = not check_conditions.empty

    if has_explicit_check:
        # Use first CHECK condition as final check
        final_check = check_conditions.iloc[0]
        # All other conditions are filters
        filters = rule_group[logic_values != "CHECK"]
    else:
        # Legacy behavior: use last AND as check if present
        and_conditions = rule_group[logic_values == "AND"]
        if not and_conditions.empty:
            # Get the last AND as the check
            final_check = and_conditions.iloc[-1]
            # All conditions up to the last AND are filters
            last_and_idx = and_conditions.index[-1]
            filters = rule_group[rule_group.index < last_and_idx]
        else:
            # No AND conditions found, just use WHERE as filter
            filters = rule_group
            final_check = rule_group.iloc[0]  # Default to first condition as check

    return filters, final_check


def process_rule(
    speckle_objects: list[Base], rule_group: pd.DataFrame
) -> tuple[list[Any], list[Any]] | tuple[list[Base], list[Base]]:
    """Processes a rule group against a list of Speckle objects.

    This function implements the "filter then validate" approach:
    1. Apply filter conditions sequentially to narrow down objects
    2. Apply the final check condition to determine pass/fail

    This approach is efficient for large models as it reduces the number
    of objects that need full validation.

    Args:
        speckle_objects: List of Speckle objects to be processed
        rule_group: DataFrame defining the filter and check conditions

    Returns:
        A tuple of lists (pass_objects, fail_objects)
    """
    if not speckle_objects or rule_group.empty:
        return [], []

    try:
        validate_rule_structure(rule_group)
    except ValueError as e:
        speckle_print(f"Rule validation error: {str(e)}")
        return [], []

    # Get filters and final check
    filters, final_check = get_filters_and_check(rule_group)

    # Start with all objects
    filtered_objects = speckle_objects.copy()
    rule_number = rule_group.iloc[0]["Rule Number"]

    #  Apply each filter condition sequentially
    for index, (_, filter_condition) in enumerate(filters.iterrows()):
        filtered_objects = [
            obj
            for obj in filtered_objects
            if evaluate_condition(
                speckle_object=obj, condition=filter_condition, rule_number=rule_number, case_number=index
            )
        ]

        # Early exit if no objects pass filters
        if not filtered_objects:
            return [], []

    # For remaining objects, evaluate the final check
    # This separates objects into pass/fail groups
    pass_objects = []
    fail_objects = []

    for obj in filtered_objects:
        if evaluate_condition(
            speckle_object=obj, condition=final_check, rule_number=rule_number, case_number=len(filters)
        ):
            pass_objects.append(obj)
        else:
            fail_objects.append(obj)

    return pass_objects, fail_objects


def apply_rules_to_objects(
    speckle_objects: list[Base],
    grouped_rules: DataFrameGroupBy,
    automate_context: AutomationContext,
    minimum_severity: MinimumSeverity = MinimumSeverity.INFO,
    hide_skipped: bool = False,
) -> dict[str, tuple[list[Base], list[Base]]]:
    """Applies defined rules to a list of objects and updates the automate context with the results.

    This is the main orchestration function that:
    1. Processes each rule group against all objects
    2. Filters results based on severity levels
    3. Attaches results to objects in the Speckle Automate context
    4. Reports skipped rules (where no objects matched filters)

    Args:
        speckle_objects: The list of objects to which rules are applied
        grouped_rules: The rules grouped by rule number
        automate_context: Context manager for attaching results to objects
        minimum_severity: Minimum severity level to report
        hide_skipped: Whether to hide skipped rules in results

    Returns:
        Dictionary mapping rule IDs to (pass_objects, fail_objects) tuples
    """
    grouped_results = {}
    rules_processed = 0
    severity_levels = {MinimumSeverity.INFO: 0, MinimumSeverity.WARNING: 1, MinimumSeverity.ERROR: 2}
    min_severity_level = severity_levels[minimum_severity]

    for rule_id, rule_group in grouped_rules:
        rule_id_str = str(rule_id)  # Convert rule_id to string
        rules_processed += 1

        # Ensure rule_group has necessary columns
        if "Message" not in rule_group.columns or "Report Severity" not in rule_group.columns:
            continue  # Or raise an exception if these columns are mandatory

        pass_objects, fail_objects = process_rule(speckle_objects, rule_group)

        # Get the severity level for this rule
        rule_severity = get_severity(rule_group.iloc[-1])
        rule_severity_level = severity_levels[MinimumSeverity(rule_severity.value)]

        # For passing objects, only attach if we're showing all levels (INFO)
        if minimum_severity == MinimumSeverity.INFO:
            attach_results(pass_objects, rule_group.iloc[-1], rule_id_str, automate_context, True)

        # For failing objects, attach if they meet minimum severity threshold
        if rule_severity_level >= min_severity_level:
            attach_results(fail_objects, rule_group.iloc[-1], rule_id_str, automate_context, False)

        if len(pass_objects) == 0 and len(fail_objects) == 0 and not hide_skipped:
            automate_context.attach_info_to_objects(
                category=f"Rule {rule_id_str} Skipped",
                object_ids=["0"],  # This is a hack to get a rule to report with no valid objects
                message=f"No objects found for rule {rule_id_str}",
                metadata={},
            )

        grouped_results[rule_id_str] = (pass_objects, fail_objects)

    # return pass_objects, fail_objects for each rule
    return grouped_results


class SeverityLevel(Enum):
    """Enumeration for severity levels of rule results.

    These severity levels determine how rule failures are displayed:
    - INFO: Informational, no action required
    - WARNING: Potential issue that should be reviewed
    - ERROR: Critical issue requiring attention
    """

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


def get_severity(rule_info: pd.Series) -> SeverityLevel:
    """Convert a string severity level from the spreadsheet to the corresponding SeverityLevel enum.

    This function normalizes user input with robust handling for:
    - Case insensitivity (e.g., "info", "WARNING" → "Info", "Warning")
    - Shorthand mappings (e.g., "WARN" → "Warning")
    - Whitespace handling
    - Default fallback to ERROR for invalid input

    Args:
        rule_info: Series containing rule information with 'Report Severity' key

    Returns:
        Appropriate SeverityLevel enum value
    """
    severity = rule_info.get("Report Severity") or rule_info.get("Severity")  # Extract severity from input data

    # If severity is None or not a string (e.g., numeric input), default to ERROR
    if not isinstance(severity, str):
        return SeverityLevel.ERROR

    severity = severity.strip().upper()  # Remove leading/trailing spaces & normalize case

    # Define a mapping for shorthand or alternate spellings
    alias_map = {
        "WARN": "WARNING",  # Treat "WARN" as "WARNING"
    }

    # Replace shorthand values if applicable
    severity = alias_map.get(severity, severity)

    # Attempt to match with an existing SeverityLevel enum value (case-insensitive)
    return next(
        (level for level in SeverityLevel if level.value.upper() == severity),
        SeverityLevel.ERROR,  # Default to ERROR if no match is found
    )


def get_metadata(
    rule_id: str, rule_info: pd.Series, passed: bool, speckle_objects: list[Base]
) -> dict[str, str | int | Any]:
    """Generates structured metadata for rule results.

    This metadata is attached to objects in the Speckle platform and is:
    1. Validated for JSON serializability
    2. Structured for consistent representation
    3. Includes key information about the rule and results

    Args:
        rule_id: Identifier for the rule
        rule_info: Series containing rule information
        passed: Boolean indicating if the rule passed
        speckle_objects: List of Speckle objects affected

    Returns:
        Dictionary containing metadata if valid JSON serializable, empty dict otherwise
    """
    try:
        metadata = {
            "rule_id": rule_id,
            "status": "PASS" if passed else "FAIL",
            "severity": get_severity(rule_info).value,
            "rule_message": format_message(rule_info),
            "object_count": len(speckle_objects),
        }

        # Validate JSON serializability
        json.dumps(metadata)
        return metadata

    except (TypeError, ValueError, json.JSONDecodeError) as e:
        # Log the error for debugging purposes
        print(f"Error creating metadata: {str(e)}")
        return {}


def attach_results(
    speckle_objects: list[Base],
    rule_info: pd.Series,
    rule_id: str,
    context: AutomationContext,
    passed: bool,
) -> None:
    """Attaches rule results to objects in the Speckle Automate context.

    This function is the interface to the Speckle platform for reporting results:
    - For failing objects, attaches results with appropriate severity levels
    - For passing objects, attaches informational results
    - Includes structured metadata for consistent reporting

    Args:
        speckle_objects: The list of objects affected by the rule
        rule_info: Information about the rule
        rule_id: Identifier for the rule
        context: The Speckle Automate context for result attachment
        passed: Whether the objects passed the rule
    """
    if not speckle_objects:
        return

    # Create structured metadata for onward data analysis uses

    metadata = get_metadata(rule_id, rule_info, passed, speckle_objects)
    message = format_message(rule_info)

    if not passed:
        speckle_print(rule_info["Report Severity"])

        severity = (
            ObjectResultLevel.WARNING
            if rule_info["Report Severity"].capitalize() in ["Warning", "Warn"]
            else ObjectResultLevel.ERROR
        )
        context.attach_result_to_objects(
            category=f"Rule {rule_id}",
            object_ids=[speckle_object.id for speckle_object in speckle_objects],
            message=message,
            level=severity,
            metadata=metadata,
        )
    else:
        context.attach_info_to_objects(
            category=f"Rule {rule_id}",
            object_ids=[speckle_object.id for speckle_object in speckle_objects],
            message=message,
            metadata=metadata,
        )


def format_message(rule_info):
    """Format the message for the rule result.

    Handles cases where the message might be None or NaN.

    Args:
        rule_info: Series containing rule information with 'Message' key

    Returns:
        Formatted message string
    """
    message = (
        str(rule_info["Message"])
        if rule_info["Message"] is not None and not pd.isna(rule_info["Message"])
        else "No Message"
    )
    return message
