from enum import Enum
from typing import Any

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy
from speckle_automate import AutomationContext, ObjectResultLevel
from specklepy.objects.base import Base

from inputs import MinimumSeverity
from src.helpers import speckle_print
from src.predicates import PREDICATE_METHOD_MAP
from src.rules import PropertyRules


def evaluate_condition(
    speckle_object: Base, condition: pd.Series, rule_number: str | None = None, case_number: int | None = None
) -> bool:
    """Given a Speckle object and a condition, evaluates the condition and returns a boolean value.

    A condition is a pandas Series object with the following keys:
    - 'Property Name': The name of the property to evaluate.
    - 'Predicate': The predicate to use for evaluation.
    - 'Value': The value to compare against.

    Args:
        rule_number (string): For information the rule number.
        case_number (int): For information the rule clause number.
        speckle_object (Base): The Speckle object to evaluate.
        condition (pd.Series): The condition to evaluate.

    Returns:
        bool: The result of the evaluation. True if the condition is met, False otherwise.
    """
    property_name = condition["Property Name"]
    predicate_key = condition["Predicate"]
    value = condition["Value"]

    _ = rule_number
    _ = case_number

    if predicate_key in PREDICATE_METHOD_MAP:
        method_name = PREDICATE_METHOD_MAP[predicate_key]
        method = getattr(PropertyRules, method_name, None)

        if method:
            check_answer = method(speckle_object, property_name, value)

            return check_answer
    return False


def process_rule(
    speckle_objects: list[Base], rule_group: pd.DataFrame
) -> tuple[list[Any], list[Any]] | tuple[list[Base], list[Base]]:
    """Processes a set of rules against Speckle objects, returning those that pass and fail.

    The first rule is used as a filter ('WHERE'), and subsequent rules as conditions ('AND').

    Args:
        speckle_objects: List of Speckle objects to be processed.
        rule_group: DataFrame defining the filter and conditions.

    Returns:
        A tuple of lists containing objects that passed and failed the rule.
    """
    # Extract the 'WHERE' condition and subsequent 'AND' conditions
    filter_condition = rule_group.iloc[0]
    subsequent_conditions = rule_group.iloc[1:]

    # get the last row of the rule_group and get the Message and Report Severity
    rule_info = rule_group.iloc[-1]
    rule_number = rule_info["Rule Number"]

    # Filter objects based on the 'WHERE' condition
    filtered_objects = [
        speckle_object for speckle_object in speckle_objects if evaluate_condition(speckle_object, filter_condition)
    ]

    if not filtered_objects or len(list(filtered_objects)) == 0:
        return [], []

    # Initialize lists for passed and failed objects
    pass_objects, fail_objects = [], []

    # Evaluate each filtered object against the 'AND' conditions
    for speckle_object in filtered_objects:
        if all(
            evaluate_condition(
                speckle_object=speckle_object, condition=condition, rule_number=rule_number, case_number=index
            )
            for index, condition in subsequent_conditions.iterrows()
        ):
            pass_objects.append(speckle_object)
        else:
            fail_objects.append(speckle_object)

    return pass_objects, fail_objects


def apply_rules_to_objects(
    speckle_objects: list[Base],
    grouped_rules: DataFrameGroupBy,
    automate_context: AutomationContext,
    minimum_severity: MinimumSeverity = MinimumSeverity.INFO,
    hide_skipped: bool = False,
) -> dict[str, tuple[list[Base], list[Base]]]:
    """Applies defined rules to a list of objects and updates the automate context based on the results.

    Args:
        speckle_objects (List[Base]): The list of objects to which rules are applied.
        grouped_rules (pd.DataFrameGroupBy): The DataFrame containing rule definitions.
        automate_context (Any): Context manager for attaching rule results.
        minimum_severity: Minimum severity level to report
        hide_skipped: Whether to hide skipped tests
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
    """Enum for severity levels."""

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


def get_severity(rule_info: pd.Series) -> SeverityLevel:
    """Convert a string severity level to the corresponding SeverityLevel enum.

    This function normalizes input strings (because processing user entered dead is hard), handling:
    - Case insensitivity (e.g., "info", "WARNING" → "Info", "Warning")
    - Shorthand mappings (e.g., "WARN" → "Warning")
    - Stripping whitespace
    - Defaults to SeverityLevel.ERROR if the input is invalid
    """
    severity = rule_info.get("Report Severity")  # Extract severity from input data

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
    """Function that generates metadata with severity validation."""
    metadata = {
        "rule_id": rule_id,
        "status": "PASS" if passed else "FAIL",
        "severity": get_severity(rule_info).value,  # Keep proper casing
        "rule_message": rule_info["Message"],
        "object_count": len(speckle_objects),
    }
    return metadata


def attach_results(
    speckle_objects: list[Base],
    rule_info: pd.Series,
    rule_id: str,
    context: AutomationContext,
    passed: bool,
) -> None:
    """Attaches the results of a rule to the objects in the context.

    Args:
        speckle_objects (List[Base]): The list of objects to which the rule was applied.
        rule_info (pd.Series): The information about the rule.
        rule_id (str): The ID of the rule.
        context (AutomationContext): The context manager for attaching results.
        passed (bool): Whether the rule passed or failed.
    """
    if not speckle_objects:
        return

    # Create structured metadata for onward data analysis uses

    metadata = get_metadata(rule_id, rule_info, passed, speckle_objects)

    message = f"{rule_info['Message']}"

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
