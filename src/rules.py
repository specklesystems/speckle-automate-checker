"""A collection of rules for processing Speckle objects and their properties."""

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
    def is_parameter_value_contains(speckle_object: Base, parameter_name: str, substring: str) -> bool:
        """Checks if parameter value contains the given substring.

        Args:
            speckle_object: The Speckle object to check
            parameter_name: Name of the parameter to check
            substring: The substring to look for

        Returns:
            bool: True if the parameter value contains the substring
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        # Convert both to strings for comparison
        try:
            parameter_str = str(parameter_value).lower()
            substring_str = str(substring).lower()
            return substring_str in parameter_str
        except (TypeError, ValueError) as e:
            print(f"Error in is_parameter_value_contains: {e}")
            return False

    @staticmethod
    def normalize_path(path: str) -> str:
        """Remove technical path prefixes like 'properties' and 'parameters'."""
        parts = path.split(".")
        filtered = [p for p in parts if p.lower() not in ("properties", "parameters")]
        return ".".join(filtered)

    @staticmethod
    def convert_revit_boolean(value: Any) -> Any:
        """Convert Revit-style Yes/No strings to boolean values."""
        # Handle None case
        if value is None:
            return None

        # Already a boolean
        if isinstance(value, bool):
            return value

        # Handle string case with proper type checking
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower == "yes":
                return True
            if value_lower == "no":
                return False

        # Return original value if no conversion applied
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
    def find_property(root: Any, search_path: str, get_raw: bool = False) -> tuple[bool, Any]:
        """Find a property by searching through nested objects.

        Args:
            root: The root object to search
            search_path: Path to the property to find
            get_raw: Whether to return raw values without conversion

        Returns:
            Tuple of (found: bool, value: Any)
        """
        # Normalize the search path
        norm_path = PropertyRules.normalize_path(search_path)
        parts = norm_path.split(".")

        # Search through object hierarchy
        def traverse(obj: Any, visited: set[int] | None = None) -> tuple[bool, Any]:
            if visited is None:
                visited = set()

            # Skip if already visited or not a container type
            if not isinstance(obj, dict | Base):
                return False, None

            obj_id = id(obj)
            if obj_id in visited:
                return False, None

            visited.add(obj_id)

            # Try direct path match
            found, value = PropertyRules.search_obj(obj, parts)
            if found:
                return True, PropertyRules.get_obj_value(value, get_raw)

            # Handle dict
            if isinstance(obj, dict):
                for key, val in obj.items():
                    if isinstance(val, dict | Base):
                        found, value = traverse(val, visited)
                        if found:
                            return True, value

            # Handle Base
            elif isinstance(obj, Base):
                for key in obj.get_member_names():
                    if not key.startswith("_"):
                        val = getattr(obj, key)
                        if isinstance(val, dict | Base):
                            found, value = traverse(val, visited)
                            if found:
                                return True, value

            visited.remove(obj_id)  # Clean up visited set
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
        get_raw: bool = False,
    ) -> Any:
        """Get a parameter value from the Speckle object using strict path matching.

        Args:
            speckle_object: The Speckle object to search
            parameter_name: Exact parameter path to find
            default_value: Value to return if parameter not found
            get_raw: Whether to return raw values without conversion

        Returns:
            The parameter value if found using exact path matching, otherwise default_value
        """
        found, value = PropertyRules.find_property(speckle_object, parameter_name, get_raw)
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
        """Checks if parameter value is greater than threshold.

        Note: From a UX perspective, if someone writes 'height greater than 2401',
        they mean "flag an error if height <= 2401". So we flip the comparison.
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        try:
            parameter_value = float(parameter_value)
        except (ValueError, TypeError):
            return False  # Return False if the value cannot be converted to a number
        return parameter_value > PropertyRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_less_than(speckle_object: Base, parameter_name: str, threshold: str) -> bool:
        """Checks if parameter value is less than threshold.

        Note: From a UX perspective, if someone writes 'height less than 2401',
        they mean "flag an error if height >= 2401". So we flip the comparison.
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        try:
            parameter_value = float(parameter_value)
        except (ValueError, TypeError):
            return False  # Return False if the value cannot be converted to a number

        return parameter_value < PropertyRules.parse_number_from_string(threshold)

    @staticmethod
    def is_parameter_value_in_range(speckle_object: Base, parameter_name: str, value_range: str) -> bool:
        """Checks if parameter value falls outside specified range.

        Note: From a UX perspective, if someone writes 'height in range 2401,3000',
        they mean "flag an error if height < 2401 or height > 3000".
        """
        min_value, max_value = value_range.split(",")
        min_value = PropertyRules.parse_number_from_string(min_value)
        max_value = PropertyRules.parse_number_from_string(max_value)

        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False
        try:
            parameter_value = float(parameter_value)
        except (ValueError, TypeError):
            return False  # Return False if the value cannot be converted to a number

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
            value_list = [v.strip() for v in value_list.split(",") if v.strip()]

        def is_value_in_list(value: Any, my_list: Any) -> bool:
            if isinstance(my_list, list):
                return value in my_list or str(value) in my_list
            return False

        return is_value_in_list(parameter_value, value_list)

    @staticmethod
    def check_boolean_value(value: Any, values_to_match: tuple[str, ...]) -> bool:
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
        return PropertyRules.check_boolean_value(parameter_value, ("yes", "true", "1"))

    @staticmethod
    def is_parameter_value_false(speckle_object: Base, parameter_name: str) -> bool:
        """Check if parameter value represents false."""
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        return PropertyRules.check_boolean_value(parameter_value, ("no", "false", "0"))

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
    def try_boolean_comparison(value1: Any, value2: Any, allow_yes_no: bool) -> tuple[bool, bool]:
        """Attempts to compare two values as booleans."""

        def strict_convert_boolean(value: Any) -> Any:
            """Convert 'True'/'False' strings to booleans, and use `convert_revit_boolean` for Yes/No."""
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                value_lower = value.strip().lower()
                if value_lower == "true":
                    return True
                if value_lower == "false":
                    return False
                # Use convert_revit_boolean for Yes/No conversion
                return PropertyRules.convert_revit_boolean(value) if allow_yes_no else value

            return value

        bool1 = strict_convert_boolean(value1)
        bool2 = strict_convert_boolean(value2)

        # If both are valid booleans, compare them
        if isinstance(bool1, bool) and isinstance(bool2, bool):
            return True, bool1 == bool2

        return False, False

    @staticmethod
    def compare_values(
        value1: Any,
        value2: Any,
        case_sensitive: bool = False,
        tolerance: float = 1e-6,
        allow_yes_no_bools: bool = True,
        use_exact: bool = False,
    ) -> bool:
        """Core logic for comparing two values with type handling and tolerance.

        Args:
            value1: First value to compare
            value2: Second value to compare
            case_sensitive: Whether to perform case-sensitive string comparison
            tolerance: Tolerance for floating point comparisons
            allow_yes_no_bools: Whether to convert Yes/No strings to booleans when comparing with boolean values
            use_exact: Whether to use exact equality for numeric comparisons
        Returns:
            bool: True if values are considered equal, False otherwise
        """
        # Try boolean comparison first
        can_compare, result = PropertyRules.try_boolean_comparison(value1, value2, allow_yes_no_bools)
        if can_compare:
            return result

        # Handle case where one value is a string that can be interpreted as a number
        def safe_convert_to_number(val):
            if isinstance(val, str):
                val = val.strip()  # Remove whitespace
                if val.replace(".", "", 1).replace("-", "", 1).isdigit():  # Handle negative numbers
                    return float(val)
            return val

        value1 = safe_convert_to_number(value1)
        value2 = safe_convert_to_number(value2)

        # For strings: Allow case insensitivity if specified
        if isinstance(value1, str) and isinstance(value2, str):
            if not case_sensitive:
                return value1.lower() == value2.lower()
            return value1 == value2

        # For floats and ints, check using math.isclose for floating-point precision
        if isinstance(value1, float | int) and isinstance(value2, float | int):
            if use_exact:
                return value1 == value2  # Strict equality for identical comparisons
            return math.isclose(value1, value2, abs_tol=tolerance)

        # Fallback: Use regular equality for other cases
        return value1 == value2

    @staticmethod
    def is_equal_value(
        speckle_object: Base,
        parameter_name: str,
        value_to_match: Any,
        case_sensitive: bool = False,
        tolerance: float = 1e-6,
    ) -> bool:
        """Compares a parameter value from a Speckle object with the provided value.

        Args:
            speckle_object (Base): The Speckle object containing the parameter
            parameter_name (str): Name of the parameter to compare
            value_to_match: The value to compare against (float, string, int, etc.)
            case_sensitive (bool): Whether to perform case-sensitive comparison for strings
            tolerance (float): Tolerance for floating point comparisons

        Returns:
            bool: True if values are considered equal, False otherwise
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return False

        return PropertyRules.compare_values(
            parameter_value, value_to_match, case_sensitive, tolerance, allow_yes_no_bools=True
        )

    @staticmethod
    def is_not_equal_value(
        speckle_object: Base,
        parameter_name: str,
        value_to_match: Any,
        case_sensitive: bool = False,
        tolerance: float = 1e-6,
    ) -> bool:
        """Checks if a parameter value from a Speckle object is not equal to the provided value.

        Args:
            speckle_object (Base): The Speckle object containing the parameter
            parameter_name (str): Name of the parameter to compare
            value_to_match: The value to compare against (float, string, int, etc.)
            case_sensitive (bool): Whether to perform case-sensitive comparison for strings
            tolerance (float): Tolerance for floating point comparisons

        Returns:
            bool: True if values are not equal or parameter doesn't exist, False if they are equal
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
        if parameter_value is None:
            return True  # Non-existent parameters are considered not equal

        return not PropertyRules.compare_values(
            parameter_value, value_to_match, case_sensitive, tolerance, allow_yes_no_bools=True
        )

    @staticmethod
    def is_identical_value(speckle_object: Base, parameter_name: str, value_to_match: Any) -> bool:
        """Checks if a parameter value from a Speckle object is exactly identical to the provided value.

        Uses strict comparison with no type coercion, case sensitivity, or Yes/No conversion.

        Args:
            speckle_object (Base): The Speckle object containing the parameter
            parameter_name (str): Name of the parameter to compare
            value_to_match: The value to compare against

        Returns:
            bool: True if values are identical, False otherwise
        """
        parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name, get_raw=True)
        if parameter_value is None:
            return False

        return PropertyRules.compare_values(
            parameter_value, value_to_match, case_sensitive=True, tolerance=0, allow_yes_no_bools=False, use_exact=True
        )
