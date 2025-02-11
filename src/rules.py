import math
import re
from typing import Any

from Levenshtein import ratio
from specklepy.objects.base import Base

PRIMITIVE_TYPES = (bool, int, float, str, type(None))


class Rules:
    """A collection of rules for processing properties in Speckle objects."""

    @staticmethod
    def try_get_display_value(
        speckle_object: Base,
    ) -> list[Base] | None:
        """Try fetching the display value from a Speckle object."""
        raw_display_value = getattr(speckle_object, "displayValue", None) or getattr(
            speckle_object, "@displayValue", None
        )

        if raw_display_value is None:
            return None

        display_values = [value for value in raw_display_value if isinstance(value, Base)]

        if not display_values:
            return None

        return display_values

    @staticmethod
    def is_displayable_object(speckle_object: Base) -> bool:
        """Determines if a given Speckle object is displayable."""
        display_values = Rules.try_get_display_value(speckle_object)
        if display_values and getattr(speckle_object, "id", None) is not None:
            return True

        definition = getattr(speckle_object, "definition", None)
        if definition:
            definition_display_values = Rules.try_get_display_value(definition)
            if definition_display_values and getattr(definition, "id", None) is not None:
                return True

        return False

    @staticmethod
    def get_displayable_objects(flat_list_of_objects: list[Base]) -> list[Base]:
        """Filters a list of Speckle objects to only include displayable objects."""
        return [
            speckle_object
            for speckle_object in flat_list_of_objects
            if Rules.is_displayable_object(speckle_object) and getattr(speckle_object, "id", None)
        ]


class PropertyRules:
    """A collection of rules for processing parameters in Speckle objects."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Remove technical path prefixes like 'properties' and 'parameters'."""
        parts = path.split(".")
        filtered = [p for p in parts if p.lower() not in ("properties", "parameters")]
        return ".".join(filtered)

    @staticmethod
    def convert_revit_boolean(value: Any) -> Any:
        """Convert Revit-style Yes/No strings to boolean values."""
        if isinstance(value, str):
            if value.lower() == "yes":
                return True
            if value.lower() == "no":
                return False
        return value

    @staticmethod
    def get_obj_value(obj: Any, get_raw: bool = False) -> Any:
        """Extract appropriate value from an object, handling special cases."""
        if get_raw:
            return obj

        # Handle primitive types directly
        if isinstance(obj, PRIMITIVE_TYPES):
            return PropertyRules.convert_revit_boolean(obj)

        # Handle dict
        if isinstance(obj, dict):
            if "value" in obj:
                return PropertyRules.convert_revit_boolean(obj["value"])
            return obj

        # Handle Base object
        if isinstance(obj, Base):
            if hasattr(obj, "value"):
                return PropertyRules.convert_revit_boolean(obj.value)
            return obj

        return obj

    @staticmethod
    def search_obj(obj: Any, parts: list[str]) -> tuple[bool, Any]:
        """Recursively search an object following a path."""
        if not parts:
            return True, obj

        current = parts[0]
        remaining = parts[1:]

        # Handle dict
        if isinstance(obj, dict):
            for key in obj:
                if key.lower() == current.lower():
                    if remaining:
                        return PropertyRules.search_obj(obj[key], remaining)
                    return True, obj[key]

        # Handle Base
        elif isinstance(obj, Base):
            for key in obj.get_member_names():
                if key.lower() == current.lower():
                    if remaining:
                        return PropertyRules.search_obj(getattr(obj, key), remaining)
                    return True, getattr(obj, key)

        return False, None

    @staticmethod
    def find_property(root: Any, search_path: str) -> tuple[bool, Any]:
        """Find a property by searching through nested objects."""
        # Normalize the search path
        norm_path = PropertyRules.normalize_path(search_path)
        parts = norm_path.split(".")

        # Search through object hierarchy
        def traverse(obj: Any) -> tuple[bool, Any]:
            # Try direct path match
            found, value = PropertyRules.search_obj(obj, parts)
            if found:
                return True, PropertyRules.get_obj_value(value)

            # Handle dict
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if isinstance(val, dict | Base):
                        found, value = traverse(val)
                        if found:
                            return True, value

            # Handle Base
            elif isinstance(obj, Base):
                for key in obj.get_member_names():
                    if not key.startswith("_"):
                        val = getattr(obj, key)
                        if isinstance(val, dict | Base):
                            found, value = traverse(val)
                            if found:
                                return True, value

            return False, None

        return traverse(root)

    @staticmethod
    def has_parameter(speckle_object: Base, parameter_name: str, *_args, **_kwargs) -> bool:
        """Check if a parameter exists in the Speckle object."""
        found, _ = PropertyRules.find_property(speckle_object, parameter_name)
        return found

    @staticmethod
    def get_parameter_value(
        speckle_object: Base,
        parameter_name: str,
        default_value: Any = None,
    ) -> Any:
        """Get a parameter value from the Speckle object using strict path matching.

        Args:
            speckle_object: The Speckle object to search
            parameter_name: Exact parameter path to find
            default_value: Value to return if parameter not found

        Returns:
            The parameter value if found using exact path matching, otherwise default_value
        """
        found, value = PropertyRules.find_property(speckle_object, parameter_name)
        return value if found else default_value

    @staticmethod
    def is_parameter_value(speckle_object: Base, parameter_name: str, value_to_match: Any) -> bool:
        """Checks if the value of the specified parameter matches the given value."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return parameter_value == value_to_match

    @staticmethod
    def parse_number_from_string(input_string: str):
        """Attempts to parse a number from a string."""
        try:
            return int(input_string)
        except ValueError:
            try:
                return float(input_string)
            except ValueError:
                raise ValueError("Input string is not a valid integer or float")

    @staticmethod
    def is_parameter_value_greater_than(speckle_object: Base, parameter_name: str, threshold: str) -> bool:
        """Checks if parameter value is greater than threshold."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, int | float):
            raise ValueError(f"Parameter value must be a number, got {type(parameter_value)}")
        return parameter_value > PropertyRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_less_than(speckle_object: Base, parameter_name: str, threshold: str) -> bool:
        """Checks if parameter value is less than threshold."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        if not isinstance(parameter_value, int | float):
            raise ValueError(f"Parameter value must be a number, got {type(parameter_value)}")
        return parameter_value < PropertyRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_in_range(speckle_object: Base, parameter_name: str, value_range: str) -> bool:
        """Checks if parameter value falls within range."""
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
    def is_parameter_value_like(
        speckle_object: Base,
        parameter_name: str,
        pattern: str,
        fuzzy: bool = False,
        threshold: float = 0.8,
    ) -> bool:
        """Checks if parameter value matches pattern."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        if fuzzy:
            similarity = ratio(str(parameter_value), pattern)
            return similarity >= threshold
        else:
            return bool(re.match(pattern, str(parameter_value)))

    @staticmethod
    def is_parameter_value_in_list(speckle_object: Base, parameter_name: str, value_list: list[Any] | str) -> bool:
        """Checks if parameter value is in list."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)

        if isinstance(value_list, str):
            value_list = [value.strip() for value in value_list.split(",")]

        def is_value_in_list(value: Any, my_list: Any) -> bool:
            if isinstance(my_list, list):
                return value in my_list or str(value) in my_list
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
        """Check if parameter value represents true."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return PropertyRules._check_boolean_value(parameter_value, ("yes", "true", "1"))

    @staticmethod
    def is_parameter_value_false(speckle_object: Base, parameter_name: str) -> bool:
        """Check if parameter value represents false."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return PropertyRules._check_boolean_value(parameter_value, ("no", "false", "0"))

    @staticmethod
    def has_category(speckle_object: Base) -> bool:
        """Check if object has category."""
        return PropertyRules.has_parameter(speckle_object, "category")

    @staticmethod
    def is_category(speckle_object: Base, category_input: str) -> bool:
        """Check if object matches category."""
        category_value = PropertyRules.get_parameter_value(speckle_object, "category")
        return category_value == category_input

    @staticmethod
    def get_category_value(speckle_object: Base) -> str:
        """Get object's category value."""
        return PropertyRules.get_parameter_value(speckle_object, "category")

    @staticmethod
    def is_equal_value(value1: Any, value2: Any, case_sensitive: bool = False) -> bool:
        """Compares two values with more robust handling for various types and tolerances.

        Args:
            value1: The first value to compare (can be a float, string, int, etc.).
            value2: The second value to compare (can be a float, string, int, etc.).
            case_sensitive (bool): Whether to perform case-sensitive comparison for strings. Default is False.

        Returns:
            bool: True if values are considered equal, False otherwise.
        """
        # Handle case where one value is a string that can be interpreted as a number
        if isinstance(value1, str) and value1.replace(".", "", 1).isdigit():
            value1 = float(value1)

        if isinstance(value2, str) and value2.replace(".", "", 1).isdigit():
            value2 = float(value2)

        # For strings: Allow case insensitivity if specified
        if isinstance(value1, str) and isinstance(value2, str):
            if not case_sensitive:
                return value1.lower() == value2.lower()
            return value1 == value2

        # For floats and ints, we check using math.isclose for floating-point precision
        if isinstance(value1, (float, int)) and isinstance(value2, (float, int)):
            return math.isclose(value1, value2, abs_tol=1e-6)

        # Fallback: Use regular equality for other cases
        return value1 == value2

    @staticmethod
    def is_not_equal_value(value1: Any, value2: Any) -> bool:
        """Checks if two values are not equal."""
        return not PropertyRules.is_equal_value(value1, value2)

    @staticmethod
    def is_identical_value(value1: Any, value2: Any) -> bool:
        """Checks if two values are exactly identical.

        Considering case-sensitivity and no tolerance for floating-point errors.
        """
        if isinstance(value1, str) and isinstance(value2, str):
            return value1 == value2  # Case-sensitive comparison for strings
        elif isinstance(value1, float) and isinstance(value2, float):
            # No tolerance for floating-point errors
            return value1 == value2
        return value1 == value2

    @staticmethod
    def is_not_identical_value(value1: Any, value2: Any) -> bool:
        """Checks if two values are not identical."""
        return not PropertyRules.is_identical_value(value1, value2)
