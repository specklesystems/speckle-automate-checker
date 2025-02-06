from typing import List, Optional, Tuple, Any, cast
from speckle_automate import AutomationContext, ObjectResultLevel
from specklepy.objects.base import Base
from Levenshtein import ratio
import pandas as pd
import re

from helpers import speckle_print


# We're going to define a set of rules that will allow us to filter and
# process parameters in our Speckle objects. These rules will be encapsulated
# in a class called `ParameterRules`.


class Rules:
    """
    A collection of rules for processing properties in Speckle objects.

    Simple rules can be straightforwardly implemented as static methods that
    return boolean value to be used either as a filter or a condition.
    These can then be abstracted into returning lambda functions that  we can
    use in our main processing logic. By encapsulating these rules, we can easily
    extend or modify them in the future.
    """

    @staticmethod
    def try_get_display_value(
            speckle_object: Base,
    ) -> Optional[List[Base]]:
        """Try fetching the display value from a Speckle object.

        This method encapsulates the logic for attempting to retrieve the display value from a Speckle object.
        It returns a list containing the display values if found, otherwise it returns None.

        Args:
            speckle_object (Base): The Speckle object to extract the display value from.

        Returns:
            Optional[List[Base]]: A list containing the display values. If no display value is found,
                                   returns None.
        """
        # Attempt to get the display value from the speckle_object
        raw_display_value = getattr(speckle_object, "displayValue", None) or getattr(
            speckle_object, "@displayValue", None
        )

        # If no display value found, return None
        if raw_display_value is None:
            return None

        # If display value found, filter out non-Base objects
        display_values = [
            value for value in raw_display_value if isinstance(value, Base)
        ]

        # If no valid display values found, return None
        if not display_values:
            return None

        return display_values

    @staticmethod
    def is_displayable_object(speckle_object: Base) -> bool:
        """
        Determines if a given Speckle object is displayable.

        This method encapsulates the logic for determining if a Speckle object is displayable.
        It checks if the speckle_object has a display value and returns True if it does, otherwise it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.

        Returns:
            bool: True if the object has a display value, False otherwise.
        """
        # Check for direct displayable state using try_get_display_value
        display_values = Rules.try_get_display_value(speckle_object)
        if display_values and getattr(speckle_object, "id", None) is not None:
            return True

        # Check for displayable state via definition, using try_get_display_value on the definition object
        definition = getattr(speckle_object, "definition", None)
        if definition:
            definition_display_values = Rules.try_get_display_value(definition)
            if (
                    definition_display_values
                    and getattr(definition, "id", None) is not None
            ):
                return True

        return False


def get_displayable_objects(flat_list_of_objects: List[Base]) -> List[Base]:
    # modify this lambda from before to use the static method from the Checks class
    return [
        speckle_object
        for speckle_object in flat_list_of_objects
        if Rules.is_displayable_object(speckle_object)
           and getattr(speckle_object, "id", None)
    ]

    # and the same logic that could be modified to traverse a tree of objects


def filter_objects_by_category(
        speckle_objects: List[Base], category_input: str
) -> Tuple[List[Base], List[Base]]:
    """
    Filters objects by category value and test.

    This function takes a list of Speckle objects, filters out the objects
    with a matching category value and satisfies the test, and returns
    both the matching and non-matching objects.

    Args:
        speckle_objects (List[Base]): The list of Speckle objects to filter.
        category_input (str): The category value to match against.

    Returns:
        Tuple[List[Base], List[Base]]: A tuple containing two lists:
                                        - The first list contains objects with matching category and test.
                                        - The second list contains objects without matching category or test.
    """
    matching_objects = []
    non_matching_objects = []

    for obj in speckle_objects:
        if RevitRules.is_category(obj, category_input):
            matching_objects.append(obj)
        else:
            non_matching_objects.append(obj)

    return matching_objects, non_matching_objects


class RevitRules:
    @staticmethod
    def has_parameter(
            speckle_object: Base, parameter_name: str, *_args, **_kwargs
    ) -> bool:
        """
        Checks if the speckle_object has a Revit parameter with the given name.

        This method checks if the speckle_object has a parameter with the specified name,
        considering the following cases:
        1. The parameter is a named property at the root object level.
        2. The parameter is stored as a key in the "parameters" dictionary.
        3. The parameter is stored as a nested dictionary within the "parameters" property,
           and the parameter name is stored as the value of the "name" property within each nested dictionary.

        If the parameter exists, it returns True; otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check for.
            *_args: Extra positional arguments which are ignored.
            **_kwargs: Extra keyword arguments which are ignored.

        Returns:
            bool: True if the object has the parameter, False otherwise.
        """
        if hasattr(speckle_object, parameter_name):
            return True

        parameters = cast(Base, getattr(speckle_object, "parameters", None))

        if parameters is None:
            return False

        # the parameters object can function like a dict but isn't one.
        # convert a Base object to a dict
        parameters_dict = {}

        for parameter_key in parameters.get_dynamic_member_names():
            parameters_dict[parameter_key] = getattr(parameters, parameter_key, None)

        if parameter_name in parameters_dict:
            return True

        return any(
            getattr(param_value, "name", None) == parameter_name
            for param_value in parameters_dict.values()
        )

    @staticmethod
    def get_parameter_value(
            speckle_object: Base,
            parameter_name: str,
            default_value: Any = None,
    ) -> Any | None:
        """
        Retrieves the value of the specified Revit parameter from the speckle_object.

        This method checks if the speckle_object has a parameter with the specified name,
        considering the following cases:
        1. The parameter is a named property at the root object level.
        2. The parameter is stored as a key in the "parameters" dictionary.
        3. The parameter is stored as a nested dictionary within the "parameters" property,
           and the parameter name is stored as the value of the "name" property within each nested dictionary.

        If the parameter exists and its value is not None or the specified default_value, it returns the value.
        If the parameter does not exist or its value is None or the specified default_value, it returns None.

        Args:
            speckle_object (Base): The Speckle object to retrieve the parameter value from.
            parameter_name (str): The name of the parameter to retrieve the value for.
            default_value: The default value to compare against. If the parameter value matches this value,
                           it will be treated the same as None.

        Returns:
            The value of the parameter if it exists and is not None or the specified default_value, or None otherwise.
        """
        # Attempt to retrieve the parameter from the root object level
        value = getattr(speckle_object, parameter_name, None)
        if value not in [None, default_value]:
            return value

        # If the "parameters" attribute is a Base object, extract its dynamic members
        parameters = getattr(speckle_object, "parameters", None)
        if parameters is None:
            return None

        # Prepare a dictionary of parameter values from the dynamic members of the parameters attribute
        parameters_dict = {
            key: getattr(parameters, key)
            for key in parameters.get_dynamic_member_names()
        }

        # Search for a direct match or a nested match in the parameters dictionary
        param_value = parameters_dict.get(parameter_name)
        if param_value is not None:
            if isinstance(param_value, Base):
                # Extract the nested value from a Base object if available
                nested_value = getattr(param_value, "value", None)
                if nested_value not in [None, default_value]:
                    return nested_value
            elif param_value not in [None, default_value]:
                return param_value

        # Use a generator to find the first matching 'value' for shared parameters stored in Base objects
        return next(
            (
                getattr(p, "value", None)
                for p in parameters_dict.values()
                if isinstance(p, Base) and getattr(p, "name", None) == parameter_name
            ),
            None,
        )

    from typing import Any, Union, List

    @staticmethod
    def is_parameter_value(
            speckle_object: Base, parameter_name: str, value_to_match: Any
    ) -> bool:
        """
        Checks if the value of the specified parameter matches the given value.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_to_match (Any): The value to match against.

        Returns:
            bool: True if the parameter value matches the given value, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value == value_to_match

    @staticmethod
    def is_parameter_value_like(
            speckle_object: Base,
            parameter_name: str,
            pattern: str,
            fuzzy: bool = False,
            threshold: float = 0.8,
    ) -> bool:
        """
        Checks if the value of the specified parameter matches the given pattern.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            pattern (str): The pattern to match against.
            fuzzy (bool): If True, performs fuzzy matching using Levenshtein distance.
                          If False (default), performs exact pattern matching using regular expressions.
            threshold (float): The similarity threshold for fuzzy matching (default: 0.8).
                               Only applicable when fuzzy=True.

        Returns:
            bool: True if the parameter value matches the pattern (exact or fuzzy), False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        if fuzzy:
            similarity = ratio(str(parameter_value), pattern)
            return similarity >= threshold
        else:
            return bool(re.match(pattern, str(parameter_value)))

    @staticmethod
    def parse_number_from_string(input_string: str):
        """
        Attempts to parse an integer or float from a given string.

        Args:
            input_string (str): The string containing the number to be parsed.

        Returns:
            int or float: The parsed number, or raises ValueError if parsing is not possible.
        """
        try:
            # First try to convert it to an integer
            return int(input_string)
        except ValueError:
            # If it fails to convert to an integer, try to convert to a float
            try:
                return float(input_string)
            except ValueError:
                # Raise an error if neither conversion is possible
                raise ValueError("Input string is not a valid integer or float")

    @staticmethod
    def is_parameter_value_greater_than(
            speckle_object: Base, parameter_name: str, threshold: str
    ) -> bool:
        """
        Checks if the value of the specified parameter is greater than the given threshold.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            threshold (Union[int, float]): The threshold value to compare against.

        Returns:
            bool: True if the parameter value is greater than the threshold, False otherwise.
        """

        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )
        return parameter_value > RevitRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_less_than(
            speckle_object: Base, parameter_name: str, threshold: str
    ) -> bool:
        """
        Checks if the value of the specified parameter is less than the given threshold.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            threshold (Union[int, float]): The threshold value to compare against.

        Returns:
            bool: True if the parameter value is less than the threshold, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )
        return parameter_value < RevitRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_in_range(
            speckle_object: Base, parameter_name: str, range: str
    ) -> bool:
        """
        Checks if the value of the specified parameter falls within the given range.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            range (str): The range to check against, in the format "min_value, max_value".

        Returns:
            bool: True if the parameter value falls within the range (inclusive), False otherwise.
        """

        min_value, max_value = range.split(",")
        min_value = RevitRules.parse_number_from_string(min_value)
        max_value = RevitRules.parse_number_from_string(max_value)

        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )

        return min_value <= parameter_value <= max_value

    @staticmethod
    def is_parameter_value_in_range_expanded(
            speckle_object: Base,
            parameter_name: str,
            min_value: Union[int, float],
            max_value: Union[int, float],
            inclusive: bool = True,
    ) -> bool:
        """
        Checks if the value of the specified parameter falls within the given range.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            min_value (Union[int, float]): The minimum value of the range.
            max_value (Union[int, float]): The maximum value of the range.
            inclusive (bool): If True (default), the range is inclusive (min <= value <= max).
                              If False, the range is exclusive (min < value < max).

        Returns:
            bool: True if the parameter value falls within the range (inclusive), False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, (int, float)):
            raise ValueError(
                f"Parameter value must be a number, got {type(parameter_value)}"
            )

        return (
            min_value <= parameter_value <= max_value
            if inclusive
            else min_value < parameter_value < max_value
        )

    @staticmethod
    def is_parameter_value_in_list(
            speckle_object: Base, parameter_name: str, value_list: List[Any]
    ) -> bool:
        """
        Checks if the value of the specified parameter is present in the given list of values.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_list (List[Any]): The list of values to check against.

        Returns:
            bool: True if the parameter value is found in the list, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)

        if isinstance(value_list, str):
            value_list = [value.strip() for value in value_list.split(",")]

        # parameter_value is effectively Any type, so to find its value in the value_list
        def is_value_in_list(value: Any, my_list: Any) -> bool:
            # Ensure that my_list is actually a list
            if isinstance(my_list, list):
                return value in my_list or str(value) in my_list
            else:
                speckle_print(f"Expected a list, got {type(my_list)} instead.")
                return False

        return is_value_in_list(parameter_value, value_list)

    @staticmethod
    def is_parameter_value_true(speckle_object: Base, parameter_name: str) -> bool:
        """
        Checks if the value of the specified parameter is True.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.

        Returns:
            bool: True if the parameter value is True, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value is True

    @staticmethod
    def is_parameter_value_false(speckle_object: Base, parameter_name: str) -> bool:
        """
        Checks if the value of the specified parameter is False.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.

        Returns:
            bool: True if the parameter value is False, False otherwise.
        """
        parameter_value = RevitRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value is False

    @staticmethod
    def has_category(speckle_object: Base) -> bool:
        """
        Checks if the speckle_object has a 'category' parameter.

        This method checks if the speckle_object has a 'category' parameter.
        If the 'category' parameter exists, it returns True; otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.

        Returns:
            bool: True if the object has the 'category' parameter, False otherwise.
        """
        return RevitRules.has_parameter(speckle_object, "category")

    @staticmethod
    def is_category(speckle_object: Base, category_input: str) -> bool:
        """
        Checks if the value of the 'category' property matches the given input.

        This method checks if the 'category' property of the speckle_object
        matches the given category_input. If they match, it returns True;
        otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.
            category_input (str): The category value to compare against.

        Returns:
            bool: True if the 'category' property matches the input, False otherwise.
        """
        category_value = RevitRules.get_parameter_value(speckle_object, "category")
        return category_value == category_input

    @staticmethod
    def get_category_value(speckle_object: Base) -> str:
        """
        Retrieves the value of the 'category' parameter from the speckle_object.

        This method retrieves the value of the 'category' parameter from the speckle_object.
        If the 'category' parameter exists and its value is not None, it returns the value.
        If the 'category' parameter does not exist or its value is None, it returns an empty string.

        Args:
            speckle_object (Base): The Speckle object to retrieve the 'category' parameter value from.

        Returns:
            str: The value of the 'category' parameter if it exists and is not None, or an empty string otherwise.
        """
        return RevitRules.get_parameter_value(speckle_object, "category")


# Mapping of input predicates to the corresponding methods in RevitRules
input_predicate_mapping = {
    "exists": "has_parameter",
    "matches": "is_parameter_value",
    "greater than": "is_parameter_value_greater_than",
    "less than": "is_parameter_value_less_than",
    "in range": "is_parameter_value_in_range",
    "in list": "is_parameter_value_in_list",
    "equals": "is_parameter_value",
    "true": "is_parameter_value_true",
    "false": "is_parameter_value_false",
    "is like": "is_parameter_value_like",
}


def evaluate_condition(speckle_object: Base, condition: pd.Series) -> bool:
    """
    Given a Speckle object and a condition, evaluates the condition and returns a boolean value.
    A condition is a pandas Series object with the following keys:
    - 'Property Name': The name of the property to evaluate.
    - 'Predicate': The predicate to use for evaluation.
    - 'Value': The value to compare against.

    Args:
        speckle_object (Base): The Speckle object to evaluate.
        condition (pd.Series): The condition to evaluate.

    Returns:
        bool: The result of the evaluation. True if the condition is met, False otherwise.
    """
    property_name = condition["Property Name"]
    predicate_key = condition["Predicate"]
    value = condition["Value"]

    if predicate_key in input_predicate_mapping:
        method_name = input_predicate_mapping[predicate_key]
        method = getattr(RevitRules, method_name, None)

        # speckle_print(f"Checking {property_name} {predicate_key} {value}")

        if method:
            check_answer = method(speckle_object, property_name, value)

            return check_answer
    return False


def process_rule(
        speckle_objects: List[Base], rule_group: pd.DataFrame
) -> Tuple[List[Base], List[Base]]:
    """
    Processes a set of rules against Speckle objects, returning those that pass and fail.
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

    # Filter objects based on the 'WHERE' condition
    filtered_objects = [
        speckle_object
        for speckle_object in speckle_objects
        if evaluate_condition(speckle_object, filter_condition)
    ]

    rule_number = rule_info["Rule Number"]

    speckle_print(
        f"{ filter_condition['Logic']} {filter_condition['Property Name']} "
        f"{filter_condition['Predicate']} {filter_condition['Value']}"
    )

    speckle_print(
        f"{rule_number}: {len(list(filtered_objects))} objects passed the filter."
    )

    # Initialize lists for passed and failed objects
    pass_objects, fail_objects = [], []

    # Evaluate each filtered object against the 'AND' conditions
    for speckle_object in filtered_objects:
        if all(
                evaluate_condition(speckle_object, cond)
                for _, cond in subsequent_conditions.iterrows()
        ):
            pass_objects.append(speckle_object)
        else:
            fail_objects.append(speckle_object)

    return pass_objects, fail_objects


def apply_rules_to_objects(
        speckle_objects: List[Base],
        rules_df: pd.DataFrame,
        automate_context: AutomationContext,
) -> dict[str, Tuple[List[Base], List[Base]]]:
    """
    Applies defined rules to a list of objects and updates the automate context based on the results.

    Args:
        speckle_objects (List[Base]): The list of objects to which rules are applied.
        rules_df (pd.DataFrame): The DataFrame containing rule definitions.
        automate_context (Any): Context manager for attaching rule results.
    """
    grouped_rules = rules_df.groupby("Rule Number")

    grouped_results = {}

    for rule_id, rule_group in grouped_rules:
        rule_id_str = str(rule_id)  # Convert rule_id to string

        # Ensure rule_group has necessary columns
        if (
                "Message" not in rule_group.columns
                or "Report Severity" not in rule_group.columns
        ):
            continue  # Or raise an exception if these columns are mandatory

        pass_objects, fail_objects = process_rule(speckle_objects, rule_group)

        attach_results(
            pass_objects, rule_group.iloc[-1], rule_id_str, automate_context, True
        )
        attach_results(
            fail_objects, rule_group.iloc[-1], rule_id_str, automate_context, False
        )

        grouped_results[rule_id_str] = (pass_objects, fail_objects)

    # return pass_objects, fail_objects for each rule
    return grouped_results


def attach_results(
        speckle_objects: List[Base],
        rule_info: pd.Series,
        rule_id: str,
        context: AutomationContext,
        passed: bool,
) -> None:
    """
    Attaches the results of a rule to the objects in the context.

    Args:
        speckle_objects (List[Base]): The list of objects to which the rule was applied.
        rule_info (pd.Series): The information about the rule.
        rule_id (str): The ID of the rule.
        context (AutomationContext): The context manager for attaching results.
        passed (bool): Whether the rule passed or failed.
    """

    if not speckle_objects:
        return

    message = f"{rule_info['Message']} - {'Passed' if passed else 'Failed'}"
    if passed:
        context.attach_info_to_objects(
            category=f"Rule {rule_id} Success",
            object_ids=[speckle_object.id for speckle_object in speckle_objects],
            message=message,
        )
    else:

        speckle_print(rule_info["Report Severity"])

        severity = (
            ObjectResultLevel.WARNING
            if rule_info["Report Severity"].capitalize() == "Warning"
               or rule_info["Report Severity"].capitalize() == "Warn"
            else ObjectResultLevel.ERROR
        )
        context.attach_result_to_objects(
            category=f"Rule {rule_id} Results",
            object_ids=[speckle_object.id for speckle_object in speckle_objects],
            message=message,
            level=severity,
        )
