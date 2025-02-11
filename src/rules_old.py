import re
from typing import Any

from Levenshtein import ratio
from specklepy.objects.base import Base

from src.helpers import get_item, has_item, speckle_print
from src.inputs import PropertyMatchMode

# We're going to define a set of rules that will allow us to filter and
# process parameters in our Speckle objects. These rules will be encapsulated
# in a class called `ParameterRules`.


class Rules:
    """A collection of rules for processing properties in Speckle objects.

    Simple rules can be straightforwardly implemented as static methods that
    return boolean value to be used either as a filter or a condition.
    These can then be abstracted into returning lambda functions that  we can
    use in our main processing logic. By encapsulating these rules, we can easily
    extend or modify them in the future.
    """

    @staticmethod
    def try_get_display_value(
        speckle_object: Base,
    ) -> list[Base] | None:
        """Try fetching the display value from a Speckle object.

        This method encapsulates the logic for attempting to retrieve the display value from a
        Speckle object. It returns a list containing the display values if found,
        otherwise it returns None.

        Args:
            speckle_object (Base): The Speckle object to extract the display value from.

        Returns:
            Optional[List[Base]]: A list containing the display values.
                                  If no display value is found, returns None.
        """
        # Attempt to get the display value from the speckle_object
        raw_display_value = getattr(speckle_object, "displayValue", None) or getattr(
            speckle_object, "@displayValue", None
        )

        # If no display value found, return None
        if raw_display_value is None:
            return None

        # If display value found, filter out non-Base objects
        display_values = [value for value in raw_display_value if isinstance(value, Base)]

        # If no valid display values found, return None
        if not display_values:
            return None

        return display_values

    @staticmethod
    def is_displayable_object(speckle_object: Base) -> bool:
        """Determines if a given Speckle object is displayable.

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
            if definition_display_values and getattr(definition, "id", None) is not None:
                return True

        return False

    @staticmethod
    def get_displayable_objects(flat_list_of_objects: list[Base]) -> list[Base]:
        """Filters a list of Speckle objects to only include displayable objects.

        This function takes a list of Speckle objects and filters out the objects that are displayable.
        It returns a list containing only the displayable objects.

        Args:
            flat_list_of_objects (List[Base]): The list of Speckle objects to filter.
        """
        return [
            speckle_object
            for speckle_object in flat_list_of_objects
            if Rules.is_displayable_object(speckle_object) and getattr(speckle_object, "id", None)
        ]


class PropertyRules:
    """A collection of rules for processing Revit parameters in Speckle objects."""

    @staticmethod
    def has_parameter(speckle_object: Base, parameter_name: str, *_args, **_kwargs) -> bool:
        """Checks if the speckle_object has a parameter with the given name."""
        found, _ = ParameterSearch.lookup_parameter(speckle_object, parameter_name)
        return found

    @staticmethod
    def get_parameter_value(
        speckle_object: Base,
        parameter_name: str,
        match_mode: PropertyMatchMode = PropertyMatchMode.MIXED,
        default_value: Any = None,
    ) -> Any:
        """Gets the value of a parameter if it exists."""
        found, value = ParameterSearch.lookup_parameter(speckle_object, parameter_name, match_mode)
        return value if found else default_value

    @staticmethod
    def is_v3(speckle_object: Base) -> bool:
        """Determines if a Speckle object uses v3 parameter structure.

        Args:
            speckle_object (Base): The Speckle object to check

        Returns:
            bool: True if object uses v3 structure, False otherwise
        """
        properties = get_item(speckle_object, "properties")
        return bool(properties and has_item(properties, "Parameters"))

    # @staticmethod
    # def has_parameter(speckle_object: Base, parameter_name: str, *_args, **_kwargs) -> bool:
    #     """Checks if the speckle_object has a Revit parameter with the given name.
    #
    #     First checks direct properties, then determines if it's a v2 or v3 object structure
    #     and searches in the appropriate parameter hierarchy.
    #
    #     Args:
    #         speckle_object (Base): The Speckle object to check.
    #         parameter_name (str): The name of the parameter to check for.
    #         *_args: Extra positional arguments which are ignored.
    #         **_kwargs: Extra keyword arguments which are ignored.
    #
    #     Returns:
    #         bool: True if the object has the parameter, False otherwise.
    #     """
    #     # Check direct property first regardless of version
    #     if has_item(speckle_object, parameter_name):
    #         return True
    #
    #     if PropertyRules.is_v3(speckle_object):
    #         properties = get_item(speckle_object, "properties")
    #         parameters = get_item(properties, "Parameters")
    #         if parameters:
    #
    #             def search_v3_params(params: dict, search_name: str) -> bool:
    #                 for key, value in params.items():
    #                     if isinstance(value, dict):
    #                         # Check direct name match
    #                         if key.lower() == search_name.lower():
    #                             return True
    #                         # Check nested parameters
    #                         if search_v3_params(value, search_name):
    #                             return True
    #                 return False
    #
    #             return search_v3_params(parameters, parameter_name)
    #     else:
    #         # Handle v2 structure
    #         parameters = get_item(speckle_object, "parameters")
    #         if not parameters:
    #             return False
    #
    #         # Check direct parameter name match
    #         if has_item(parameters, parameter_name):
    #             return True
    #
    #         # Check nested parameters with name property
    #         def check_nested_name(value: Any) -> bool:
    #             if isinstance(value, dict):
    #                 return get_item(value, "name") == parameter_name
    #             return get_item(value, "name") == parameter_name if hasattr(value, "name") else False
    #
    #         return any(check_nested_name(param_value) for param_value in parameters.values() if param_value is not None)
    #
    #     return False
    #
    # @staticmethod
    # def get_parameter_value(
    #     speckle_object: Base,
    #     parameter_name: str,
    #     match_mode: PropertyMatchMode = PropertyMatchMode.MIXED,
    #     default_value: Any = None,
    # ) -> Any | None:
    #     """Retrieves the value of the specified parameter from the speckle_object.
    #
    #     First checks direct properties, then determines if it's a v2 or v3 object structure
    #     and retrieves from the appropriate parameter hierarchy.
    #
    #     Args:
    #             speckle_object (Base): The Speckle object to retrieve the parameter value from.
    #         parameter_name (str): The name of the parameter to retrieve the value for.
    #         match_mode (PropertyMatchMode): The matching mode to use for parameter lookup
    #         default_value: The default value to return if parameter not found.
    #
    #     Returns:
    #         The value of the parameter if found, else default_value.
    #     """
    #     # Check direct property first regardless of version
    #     if has_item(speckle_object, parameter_name):
    #         value = get_item(speckle_object, parameter_name)
    #         return value if value is not None else default_value
    #
    #     if PropertyRules.is_v3(speckle_object):
    #         return PropertyRules.get_v3_parameter(speckle_object, parameter_name, match_mode, default_value)
    #     else:
    #         return PropertyRules.get_v2_parameter(speckle_object, parameter_name, match_mode, default_value)

    # @staticmethod
    # def get_v2_parameter(obj: Base, name: str, mode: PropertyMatchMode, default: Any) -> Any:
    #     """Get parameter value from v2 Speckle object structure.
    #
    #     Args:
    #         obj: Speckle object to get parameter from
    #         name: Parameter name to retrieve
    #         mode: Match mode for parameter lookup
    #         default: Default value if parameter not found
    #
    #     Returns:
    #         Parameter value if found, else default
    #     """
    #     parameters = get_item(obj, "parameters")
    #     if not parameters:
    #         return default
    #
    #     if mode == PropertyMatchMode.STRICT:
    #         return PropertyRules.strict_parameter_lookup(name, parameters, default)
    #
    #     def search_params(param_dict: dict, search_name: str, fuzzy: bool) -> Any:
    #         for key, value in param_dict.items():
    #             key_match = (key.lower() == search_name.lower()) or (fuzzy and search_name.lower() in key.lower())
    #             if key_match:
    #                 # Handle both direct values and nested parameter objects
    #                 return get_item(value, "value", value)
    #         return None
    #
    #     result = search_params(parameters, name, mode == PropertyMatchMode.FUZZY)
    #     return result if result is not None else default
    #
    # @staticmethod
    # def get_v3_parameter(obj: Base, name: str, mode: PropertyMatchMode, default: Any) -> Any:
    #     """Get parameter value from v3 Speckle object structure.
    #
    #     Args:
    #         obj: Speckle object to get parameter from
    #         name: Parameter name to retrieve
    #         mode: Match mode for parameter lookup
    #         default: Default value if parameter not found
    #
    #     Returns:
    #         Parameter value if found, else default
    #     """
    #     properties = get_item(obj, "properties")
    #     if not properties or not has_item(properties, "Parameters"):
    #         return default
    #
    #     parameters = get_item(properties, "Parameters")
    #     if not parameters:
    #         return default
    #
    #     if mode == PropertyMatchMode.STRICT:
    #         return PropertyRules.strict_parameter_lookup(name, parameters, default)
    #
    #     def search_nested(data: dict, search_name: str, fuzzy: bool) -> Any:
    #         for nested_key, value in data.items():
    #             if isinstance(value, dict):
    #                 key_match = (nested_key.lower() == search_name.lower()) or (
    #                     fuzzy and search_name.lower() in nested_key.lower()
    #                 )
    #
    #                 if key_match and has_item(value, "value"):
    #                     return get_item(value, "value")
    #
    #                 nested_result = search_nested(value, search_name, fuzzy)
    #                 if nested_result is not None:
    #                     return nested_result
    #         return None
    #
    #     result = search_nested(parameters, name, mode == PropertyMatchMode.FUZZY)
    #     return result if result is not None else default
    #
    # @staticmethod
    # def strict_parameter_lookup(name: str, parameters: dict, default: Any) -> Any:
    #     """Perform strict parameter lookup following exact path.
    #
    #     Args:
    #         name: Parameter path (dot separated)
    #         parameters: Parameters dictionary
    #         default: Default value if not found
    #
    #     Returns:
    #         Parameter value if found, else default
    #     """
    #     path_parts = name.split(".")
    #     current = parameters
    #
    #     for part in path_parts:
    #         if not current or not isinstance(current, dict):
    #             return default
    #
    #         # Find exact case-insensitive match
    #         key = next((k for k in current.keys() if k.lower() == part.lower()), None)
    #         if not key:
    #             return default
    #
    #         current = get_item(current, key)
    #
    #     # Handle both direct values and parameter objects
    #     if isinstance(current, dict):
    #         return get_item(current, "value", current)
    #     return current

    @staticmethod
    def is_parameter_value(speckle_object: Base, parameter_name: str, value_to_match: Any) -> bool:
        """Checks if the value of the specified parameter matches the given value.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_to_match (Any): The value to match against.

        Returns:
            bool: True if the parameter value matches the given value, False otherwise.
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value == value_to_match

    @staticmethod
    def is_parameter_value_like(
        speckle_object: Base,
        parameter_name: str,
        pattern: str,
        fuzzy: bool = False,
        threshold: float = 0.8,
    ) -> bool:
        """Checks if the value of the specified parameter matches the given pattern.

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
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        if fuzzy:
            similarity = ratio(str(parameter_value), pattern)
            return similarity >= threshold
        else:
            return bool(re.match(pattern, str(parameter_value)))

    @staticmethod
    def parse_number_from_string(input_string: str):
        """Attempts to parse an integer or float from a given string.

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
    def is_parameter_value_greater_than(speckle_object: Base, parameter_name: str, threshold: str) -> bool:
        """Checks if the value of the specified parameter is greater than the given threshold.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            threshold (Union[int, float]): The threshold value to compare against.

        Returns:
            bool: True if the parameter value is greater than the threshold, False otherwise.
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        if not isinstance(parameter_value, int | float):
            raise ValueError(f"Parameter value must be a number, got {type(parameter_value)}")
        return parameter_value > PropertyRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_less_than(speckle_object: Base, parameter_name: str, threshold: str) -> bool:
        """Checks if the value of the specified parameter is less than the given threshold.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            threshold (Union[int, float]): The threshold value to compare against.

        Returns:
            bool: True if the parameter value is less than the threshold, False otherwise.
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, int | float):
            raise ValueError(f"Parameter value must be a number, got {type(parameter_value)}")
        return parameter_value < PropertyRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_in_range(speckle_object: Base, parameter_name: str, value_range: str) -> bool:
        """Checks if the value of the specified parameter falls within the given range.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_range (str): The range to check against, in the format "min_value, max_value".

        Returns:
            bool: True if the parameter value falls within the range (inclusive), False otherwise.
        """
        min_value, max_value = value_range.split(",")
        min_value = PropertyRules.parse_number_from_string(min_value)
        max_value = PropertyRules.parse_number_from_string(max_value)

        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, int | float):
            raise ValueError(f"Parameter value must be a number, got {type(parameter_value)}")

        return min_value <= parameter_value <= max_value

    @staticmethod
    def is_parameter_value_in_range_expanded(
        speckle_object: Base,
        parameter_name: str,
        min_value: int | float,
        max_value: int | float,
        inclusive: bool = True,
    ) -> bool:
        """Checks if the value of the specified parameter falls within the given range.

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
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, int | float):
            raise ValueError(f"Parameter value must be a number, got {type(parameter_value)}")

        return min_value <= parameter_value <= max_value if inclusive else min_value < parameter_value < max_value

    @staticmethod
    def is_parameter_value_in_list(speckle_object: Base, parameter_name: str, value_list: list[Any] | str) -> bool:
        """Checks if the value of the specified parameter is present in the given list of values.

        Args:
            speckle_object (Base): The Speckle object to check.
            parameter_name (str): The name of the parameter to check.
            value_list (List[Any]): The list of values to check against.

        Returns:
            bool: True if the parameter value is found in the list, False otherwise.
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)

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
    def _check_boolean_value(value: Any, values_to_match: tuple[str, ...]) -> bool:
        """Check if a value matches any target value in expected format."""
        if isinstance(value, bool):
            return value is (True if "true" in values_to_match else False)

        if isinstance(value, str):
            return value.lower() in values_to_match

        return False

    @staticmethod
    def is_parameter_value_true(speckle_object: Base, parameter_name: str) -> bool:
        """Check if parameter value represents true (boolean True, 'yes', 'true', '1')."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return PropertyRules._check_boolean_value(parameter_value, ("yes", "true", "1"))

    @staticmethod
    def is_parameter_value_false(speckle_object: Base, parameter_name: str) -> bool:
        """Check if parameter value represents false (boolean False, 'no', 'false', '0')."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return PropertyRules._check_boolean_value(parameter_value, ("no", "false", "0"))

    @staticmethod
    def has_category(speckle_object: Base) -> bool:
        """Checks if the speckle_object has a 'category' parameter.

        This method checks if the speckle_object has a 'category' parameter.
        If the 'category' parameter exists, it returns True; otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.

        Returns:
            bool: True if the object has the 'category' parameter, False otherwise.
        """
        return PropertyRules.has_parameter(speckle_object, "category")

    @staticmethod
    def is_category(speckle_object: Base, category_input: str) -> bool:
        """Checks if the value of the 'category' property matches the given input.

        This method checks if the 'category' property of the speckle_object
        matches the given category_input. If they match, it returns True;
        otherwise, it returns False.

        Args:
            speckle_object (Base): The Speckle object to check.
            category_input (str): The category value to compare against.

        Returns:
            bool: True if the 'category' property matches the input, False otherwise.
        """
        category_value = PropertyRules.get_parameter_value(speckle_object, "category")
        return category_value == category_input

    @staticmethod
    def get_category_value(speckle_object: Base) -> str:
        """Retrieves the value of the 'category' parameter from the speckle_object.

        This method retrieves the value of the 'category' parameter from the speckle_object.
        If the 'category' parameter exists and its value is not None, it returns the value.
        If the 'category' parameter does not exist or its value is None, it returns an empty string.

        Args:
            speckle_object (Base): The Speckle object to retrieve the 'category' parameter value from.

        Returns:
            str: The value of the 'category' parameter if it exists and is not None, or an empty string otherwise.
        """
        return PropertyRules.get_parameter_value(speckle_object, "category")


class ParameterSearch:
    """Unified parameter search functionality for Speckle objects."""

    @staticmethod
    def convert_revit_boolean(value: Any) -> Any:
        """Convert Revit-style Yes/No strings to boolean values.

        Args:
            value: The value to potentially convert

        Returns:
            bool if value is a Revit boolean string, original value otherwise
        """
        if isinstance(value, str):
            if value.lower() == "yes":
                return True
            if value.lower() == "no":
                return False
        return value

    @staticmethod
    def search_parameters(
        params: dict, search_name: str, mode: PropertyMatchMode = PropertyMatchMode.STRICT
    ) -> tuple[bool, Any]:
        """Search for parameters using consistent matching logic.

        Supports flexible property chain matching that can find paths like "Instance Parameters.Dimensions.Length"
        within longer chains like "properties.Parameters.Instance Parameters.Dimensions.Length.value".
        Uses STRICT matching by default for more predictable results.

        Args:
            params: Parameter dictionary to search
            search_name: Name of parameter to find, can be dot-separated chain
            mode: Matching mode to use (STRICT by default, or FUZZY/MIXED for looser matching)

        Returns:
            Tuple of (value_found: bool, value: Any)
        """

        def matches_name(match_key: str, target: str, match_mode: PropertyMatchMode) -> bool:
            if match_mode == PropertyMatchMode.STRICT:
                return match_key.lower() == target.lower()
            elif match_mode == PropertyMatchMode.FUZZY:
                return target.lower() in match_key.lower()
            else:  # MIXED mode
                return match_key.lower() == target.lower() or target.lower() in match_key.lower()

        def try_get_value(obj: Any) -> Any:
            """Extract value from parameter object or return as is.

            Handles both dict and Base objects, checking for 'value' property in both cases.
            Returns the 'value' if found, otherwise returns the original object.
            """
            # Handle dictionary objects
            if isinstance(obj, dict):
                return obj.get("value", obj)

            # Handle Base objects
            if isinstance(obj, Base):
                return getattr(obj, "value", obj)

            # For all other types, return as is
            return obj

        # First try property chain lookup
        if "." in search_name:
            search_parts = search_name.split(".")

            def try_match_path(current: dict, remaining_search_parts: list[str], depth: int = 0) -> tuple[bool, Any]:
                if not isinstance(current, dict):
                    return False, None

                if not remaining_search_parts:  # We've matched all parts
                    return True, try_get_value(current)

                current_search = remaining_search_parts[0]

                # Try each key at current level
                for key, item_value in current.items():
                    if matches_name(key, current_search, mode):
                        # Found a match for current part, recurse with rest
                        match_found, result = try_match_path(item_value, remaining_search_parts[1:], depth + 1)
                        if match_found:
                            return True, result

                    # If no match found and value is a dict, try searching deeper
                    if isinstance(item_value, dict):
                        match_found, result = try_match_path(item_value, remaining_search_parts, depth)
                        if match_found:
                            return True, result

                return False, None

            try:
                found, value = try_match_path(params, search_parts)
                if found:
                    return True, value
            except Exception:
                pass  # Fall through to recursive search if chain lookup fails

        # Recursive search through nested dictionaries
        def recursive_search(data: dict | Base, target: str) -> tuple[bool, Any]:
            if not isinstance(data, dict | Base):
                return False, None

            # Handle both dict and Base objects for iteration
            if isinstance(data, dict):
                items = data.items()
            else:
                items = [(k, getattr(data, k)) for k in dir(data) if not k.startswith("_")]

            # First check current level
            for key, item_value in items:
                if matches_name(key, target, mode):
                    return True, try_get_value(item_value)

            # Then check nested levels
            for _, item_value in items:
                if isinstance(item_value, dict | Base):
                    item_found, result = recursive_search(item_value, target)
                    if item_found:
                        return True, result

            return False, None

        return recursive_search(params, search_name.split(".")[-1] if "." in search_name else search_name)

    @staticmethod
    def lookup_parameter(
        obj: Base, param_name: str, mode: PropertyMatchMode = PropertyMatchMode.MIXED
    ) -> tuple[bool, Any]:
        """Unified parameter lookup for both checking existence and getting values.

        Args:
            obj: Speckle object to search
            param_name: Parameter name to find
            mode: Matching mode to use

        Returns:
            Tuple of (found: bool, value: Any)
        """
        # Check direct property first
        if has_item(obj, param_name):
            value = get_item(obj, param_name)
            # Check if the direct property has a value field
            if isinstance(value, dict) and "value" in value:
                return True, value["value"]
            return True, value

        # Handle v3 structure
        if PropertyRules.is_v3(obj):
            properties = get_item(obj, "properties")
            if not properties or not has_item(properties, "Parameters"):
                return False, None

            parameters = get_item(properties, "Parameters")
            if not parameters:
                return False, None

            return ParameterSearch.search_parameters(parameters, param_name, mode)

        # Handle v2 structure
        parameters = get_item(obj, "parameters")
        if not parameters:
            return False, None

        return ParameterSearch.search_parameters(parameters, param_name, mode)
