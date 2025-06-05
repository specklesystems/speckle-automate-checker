"""Test suite for parameter handling functionality."""

import pytest
from specklepy.objects.base import Base

from src.rules import PropertyRules


class TestParameterHandling:
    """Test suite for parameter handling functionality."""

    @pytest.fixture
    def test_objects(self) -> Base:
        """Pytest fixture to provide test objects."""
        # Create a mock Base object with the required structure
        v3_obj = Base()
        v3_obj.properties = {
            "Parameters": {
                "category": "Walls",
                "Width": 300,
                "Construction": {"Width": 300},
                "Instance Parameters": {
                    "Dimensions": {"Length": 5300.000000000001},
                    "Structural": {"Structural": {"value": "Yes"}},
                    "Room Bounding": {"value": "Yes"},
                    "top is attached": {"value": "No"},
                },
                "Type Parameters": {
                    "Structure": {"Fc24 (0)": {"thickness": 300}},
                    "Text": {"符号": {"value": "W30"}},
                },
                "Type": "W30(Fc24)",
            }
        }
        v3_obj.speckle_type = "Revit"
        return v3_obj

    def test_deserialization_structure(self, test_objects):
        """Test that objects are properly deserialized with correct structure."""
        v3_obj = test_objects

        # Check base class type
        assert isinstance(v3_obj, Base), f"Expected {v3_obj} to be an instance of Base"

        # Check v3 structure
        assert hasattr(v3_obj, "properties"), (
            "v3_obj should have 'properties' attribute"
        )
        assert v3_obj.properties is not None, "v3_obj.properties should not be None"
        assert "Parameters" in v3_obj.properties, (
            "'Parameters' key should exist in v3_obj.properties"
        )

    @pytest.mark.parametrize(
        "param_name, expected_result",
        [
            ("category", True),  # Test parameters that should exist
            ("Width", True),  # Test nested parameters
            ("non_existent_param", False),  # Test non-existent parameters
        ],
    )
    def test_v3_parameter_exists(self, test_objects, param_name, expected_result):
        """Test parameter existence checking in v3 objects."""
        v3_obj = test_objects
        assert PropertyRules.has_parameter(v3_obj, param_name) == expected_result

    @pytest.mark.parametrize(
        "param_name_1, param_name_2",
        [
            # Test direct value access
            (
                "location.length",
                "location.length",
            ),
            # Test .value key access
            (
                "Type Parameters.Text.符号",
                "Type Parameters.Text.符号.value",
            ),
        ],
    )
    def test_v3_parameter_search_equivalence(
        self,
        v3_wall,
        param_name_1,
        param_name_2,
    ):
        """Test parameter existence checking equivalence in v3 objects."""
        assert PropertyRules.get_parameter_value(
            v3_wall, param_name_1
        ) == PropertyRules.get_parameter_value(v3_wall, param_name_2)

    @pytest.mark.parametrize(
        "param_name, expected_value, default_value",
        [
            # Test direct parameters
            ("category", "Walls", None),
            # Test nested parameters - using both internal and friendly names
            ("Construction.Width", 300, None),
            # Test parameters with units
            (
                "Instance Parameters.Dimensions.Length",
                5300.000000000001,
                None,
            ),
            # Test non-existent parameters with a default value
            (
                "properties.Parameters.non_existent",
                "default",
                "default",
            ),
        ],
    )
    def test_parameter_value_retrieval(
        self,
        test_objects,
        param_name,
        expected_value,
        default_value,
    ):
        """Test parameter value retrieval from v3 objects."""
        v3_obj = test_objects
        result = PropertyRules.get_parameter_value(
            v3_obj,
            param_name,
            default_value=default_value,
        )
        assert result == expected_value

    @pytest.mark.parametrize(
        "param_name, expected_value, expected_result",
        [
            ("category", "Walls", True),  # Test exact match
            ("Width", 300, True),  # Test numeric match
            ("category", "Windows", False),  # Test non-match
        ],
    )
    def test_v3_parameter_value_matching(
        self,
        test_objects,
        param_name,
        expected_value,
        expected_result,
    ):
        """Test parameter value matching in v3 objects."""
        v3_obj = test_objects
        assert (
            PropertyRules.is_parameter_value(
                v3_obj,
                param_name,
                expected_value,
            )
            == expected_result
        )

    @pytest.mark.parametrize(
        "comparison_func, param_name, value, expected_result",
        [
            (
                PropertyRules.is_parameter_value_greater_than,
                "Width",
                "200",
                True,
            ),  # Test greater than
            (
                PropertyRules.is_parameter_value_less_than,
                "Width",
                "400",
                True,
            ),  # Test less than
            (
                PropertyRules.is_parameter_value_in_range,
                "Width",
                "200,400",
                True,
            ),  # Test in range
        ],
    )
    def test_v3_parameter_numeric_comparisons(
        self, test_objects, comparison_func, param_name, value, expected_result
    ):
        """Test numeric parameter comparisons in v3 objects."""
        v3_obj = test_objects
        assert comparison_func(v3_obj, param_name, value) == expected_result

    @pytest.mark.parametrize(
        "param_name, pattern, fuzzy, expected_result",
        [
            ("category", "^Walls$", False, True),  # Test exact pattern matches
            ("category", "Walls", True, True),  # Test fuzzy matches
            ("category", "Wall", False, True),  # Test partial pattern matches
            ("category", "^Windows$", False, False),  # Test non-matches
        ],
    )
    def test_v3_parameter_value_like(
        self, test_objects, param_name, pattern, fuzzy, expected_result
    ):
        """Test pattern matching on parameter values in v3 objects."""
        v3_obj = test_objects
        assert (
            PropertyRules.is_parameter_value_like(
                v3_obj, param_name, pattern, fuzzy=fuzzy
            )
            == expected_result
        )

    @pytest.mark.parametrize(
        "param_name, valid_list, expected_result",
        [
            (
                "category",
                ["Walls", "Windows", "Doors"],
                True,
            ),  # Test value in list
            (
                "category",
                "Walls,Windows,Doors",
                True,
            ),  # Test comma-separated string list
            (
                "category",
                ["Windows", "Doors"],
                False,
            ),  # Test value not in list
        ],
    )
    def test_v3_parameter_lists(
        self,
        test_objects,
        param_name,
        valid_list,
        expected_result,
    ):
        """Test list-based parameter checks in v3 objects."""
        v3_obj = test_objects
        assert (
            PropertyRules.is_parameter_value_in_list(
                v3_obj,
                param_name,
                valid_list,
            )
            == expected_result
        )

    @pytest.mark.parametrize(
        "param_name, expected_result",
        [
            ("Room Bounding", True),  # Test true values
            ("top is attached", False),  # Test false values
            ("Top is Attached", False),  # Case sensitivity test
        ],
    )
    def test_v3_boolean_parameters(
        self,
        test_objects,
        param_name,
        expected_result,
    ):
        """Test boolean parameter checks in v3 objects."""
        v3_obj = test_objects
        if expected_result:
            assert PropertyRules.is_parameter_value_true(v3_obj, param_name)
        else:
            assert PropertyRules.is_parameter_value_false(v3_obj, param_name)

    @pytest.mark.parametrize(
        "attribute, value, expected",
        [
            # Test numeric value comparisons
            (
                "Type Parameters.Structure.Fc24 (0).thickness",
                300,
                True,
            ),
            (
                "Instance Parameters.Dimensions.Length",
                5300.000000000002,
                True,
            ),
            (
                "Instance Parameters.Dimensions.Length",
                5300,
                True,
            ),
            # Test string value comparisons
            (
                "Type Parameters.Text.符号.value",
                "W30",
                True,
            ),
            (
                "Instance Parameters.Structural.Structural.value",
                "Yes",
                True,
            ),
            # Test non-matches
            (
                "Type Parameters.Structure.Fc24 (0).thickness",
                301,
                False,
            ),
            (
                "nonexistent_param",
                "any_value",
                False,
            ),
        ],
    )
    def test_v3_parameter_value_comparisons(
        self,
        test_objects,
        attribute,
        value,
        expected,
    ):
        """Test value comparisons using v3 wall parameters."""
        assert PropertyRules.is_equal_value(test_objects, attribute, value) == expected

    @pytest.mark.parametrize(
        "wall, attribute, value, expected",
        [
            # V3 wall tests
            (
                "v3_wall",
                "Type Parameters.Structure.Fc24 (0).thickness",
                300,
                True,
            ),
            ("v3_wall", "type", "W30(Fc24)", True),
            (
                "v3_wall",
                "Type Parameters.Structure.Fc24 (0).thickness",
                300.0001,
                False,
            ),
            (
                "v3_wall",
                "location.length",
                5300.000000000002,
                False,
            ),
            (
                "v3_wall",
                "location.length",
                5300,
                False,
            ),
        ],
    )
    def test_identical_comparisons(
        self,
        test_objects,
        wall,
        attribute,
        value,
        expected,
    ):
        """Test identical value comparisons on v3 wall."""
        if attribute == "type":
            # Use case-insensitive comparison for type parameter
            assert (
                PropertyRules.is_equal_value(
                    test_objects,
                    attribute,
                    value,
                )
                == expected
            )
        else:
            # Use strict comparison for other parameters
            assert (
                PropertyRules.is_identical_value(
                    test_objects,
                    attribute,
                    value,
                )
                == expected
            )

    @pytest.mark.parametrize(
        "wall, attribute, value",
        [
            # V3 wall tests
            (
                "v3_wall",
                "Type Parameters.Structure.Fc24 (0).thickness",
                301,
            ),
            (
                "v3_wall",
                "Type Parameters.Text.符号.value",
                "W31",
            ),
            (
                "v3_wall",
                "nonexistent_param",
                "any_value",
            ),
        ],
    )
    def test_not_equal_comparisons(
        self,
        test_objects,
        wall,
        attribute,
        value,
    ):
        """Test not equal comparisons on v3 wall."""
        assert PropertyRules.is_not_equal_value(test_objects, attribute, value)

    @pytest.mark.parametrize(
        "attribute, value, expected_equal, expected_identical",
        [
            # Test Yes/No conversion in equals (should convert)
            (
                "Instance Parameters.Structural.Structural.value",
                True,
                True,
                False,
            ),  # Yes vs True
            (
                "Instance Parameters.Structural.Structural.value",
                "Yes",
                True,
                True,
            ),  # Yes vs "Yes"
            (
                "Instance Parameters.Structural.Structural.value",
                "yes",
                True,
                False,
            ),  # Yes vs "yes"
        ],
    )
    def test_boolean_conversions(
        self,
        test_objects,
        attribute,
        value,
        expected_equal,
        expected_identical,
    ):
        """Test conversion of Yes/No strings to boolean values."""
        assert (
            PropertyRules.is_equal_value(test_objects, attribute, value)
            == expected_equal
        )
        assert (
            PropertyRules.is_identical_value(test_objects, attribute, value)
            == expected_identical
        )

    @pytest.mark.parametrize(
        "wall, attribute, expected_value",
        [
            # V3 wall tests
            (
                "v3_wall",
                "Type Parameters.Structure.Fc24 (0).thickness",
                "300",
            ),
            (
                "v3_wall",
                "Instance Parameters.Dimensions.Length",
                "5300.000000000002",
            ),
        ],
    )
    def test_numeric_string_handling(
        self,
        test_objects,
        wall,
        attribute,
        expected_value,
    ):
        """Test handling of numeric strings in v3 wall."""
        assert PropertyRules.is_equal_value(
            test_objects,
            attribute,
            expected_value,
        )

    @pytest.mark.parametrize(
        "param_name, substring, expected_result",
        [
            (
                "speckle_type",
                "Revit",
                True,
            ),  # Should pass as it does not contain Revit
            (
                "speckle_type",
                "NotPresent",
                True,
            ),  # Should pass as it doesn't contain
            (
                "speckle_type",
                "",
                False,
            ),  # Should fail as empty string is contained in any string
            (
                "non_existent",
                "anything",
                True,
            ),  # Should pass as non-existent can't contain
        ],
    )
    def test_parameter_value_not_contains(
        self,
        test_objects,
        param_name,
        substring,
        expected_result,
    ):
        """Test negative substring matching on parameter values."""
        v3_obj = test_objects
        assert (
            PropertyRules.is_parameter_value_not_containing(
                v3_obj,
                param_name,
                substring,
            )
            == expected_result
        )
