"""Test suite for parameter handling functionality."""

import os
from typing import Any

import pytest
from dotenv import load_dotenv
from speckle_automate import AutomationContext, AutomationRunData  # noqa: F401, F403

# from speckle_automate.fixtures import *  # noqa: F401, F403
from specklepy.api.client import SpeckleClient
from specklepy.core.api import operations
from specklepy.objects.base import Base
from specklepy.transports.server import ServerTransport

from helpers import speckle_print
from src.rules import PropertyRules


class TestParameterHandling:
    """Test suite for parameter handling functionality."""

    @staticmethod
    def load_test_objects(v2_wall: Any, v3_wall: Any) -> tuple[Base, Base]:
        """Load test objects from a Speckle server."""
        client = SpeckleClient(host="https://app.speckle.systems", use_ssl=True)

        load_dotenv(dotenv_path="../.env")

        client.authenticate_with_token(os.getenv("SPECKLE_TOKEN"))

        transport = ServerTransport(client=client, stream_id=os.getenv("SPECKLE_PROJECT_ID"))

        speckle_print(v2_wall)
        speckle_print(v3_wall)
        v2_obj = operations.receive("cdb18060dc48281909e94f0f1d8d3cc0", transport)
        v3_obj = operations.receive("46f06fef727d64a0bbcbd7ced51e0cd2", transport)

        # return v2_wall, v3_wall
        return v2_obj, v3_obj

    @pytest.fixture
    def test_objects(self, v2_wall: Any, v3_wall: Any) -> tuple[Base, Base]:
        """Pytest fixture to provide test objects."""
        return self.load_test_objects(v2_wall, v3_wall)

    def test_deserialization_structure(self, test_objects):
        """Test that objects are properly deserialized with correct structure."""
        v2_obj, v3_obj = test_objects

        # Check base class type
        for obj in [v2_obj, v3_obj]:
            assert isinstance(obj, Base), f"Expected {obj} to be an instance of Base"

        # Check v2 structure
        assert hasattr(v2_obj, "parameters"), "v2_obj should have 'parameters' attribute"
        assert v2_obj["parameters"] is not None, "v2_obj['parameters'] should not be None"

        # Check v3 structure
        assert hasattr(v3_obj, "properties"), "v3_obj should have 'properties' attribute"
        assert v3_obj["properties"] is not None, "v3_obj['properties'] should not be None"
        assert "Parameters" in v3_obj["properties"], "'Parameters' key should exist in v3_obj['properties']"

    @pytest.mark.parametrize(
        "param_name, expected_result",
        [
            ("category", True),  # Test parameters that should exist
            ("WALL_ATTR_WIDTH_PARAM", True),  # Test nested parameters
            ("WALL_ATTR_WIDTH_PARAM.value", True),
            ("WALL_ATTR_WIDTH_PARAM.id", True),
            ("WALL_ATTR_WIDTH_PARAM.units", True),
            ("non_existent_param", False),  # Test non-existent parameters
        ],
    )
    def test_v2_parameter_exists(self, test_objects, param_name, expected_result):
        """Test parameter existence checking in v2 objects."""
        v2_obj, _ = test_objects
        assert PropertyRules.has_parameter(v2_obj, param_name) == expected_result

    @pytest.mark.parametrize(
        "param_name",
        [
            "WALL_ATTR_WIDTH_PARAM.id",
            "WALL_ATTR_WIDTH_PARAM.value",
            "WALL_ATTR_WIDTH_PARAM",
            "WALL_ATTR_WIDTH_PARAM.units",
        ],
    )
    def test_v2_parameter_value_retrieval(self, test_objects, param_name):
        """Test parameter value retrieval in v2 objects."""
        v2_obj, _ = test_objects
        assert PropertyRules.get_parameter_value(v2_obj, param_name)

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
        _, v3_obj = test_objects
        assert PropertyRules.has_parameter(v3_obj, param_name) == expected_result

    @pytest.mark.parametrize(
        "param_name_1, param_name_2",
        [
            (
                "properties.Parameters.Instance Parameters.Dimensions.Length.value",
                "Instance Parameters.Dimensions.Length",
            ),
        ],
    )
    def test_v3_parameter_search_equivalence(self, test_objects, param_name_1, param_name_2):
        """Test parameter existence checking equivalence in v3 objects."""
        _, v3_obj = test_objects
        assert PropertyRules.get_parameter_value(v3_obj, param_name_1) == PropertyRules.get_parameter_value(
            v3_obj, param_name_2
        )

    @pytest.mark.parametrize(
        "obj_version, param_name, expected_value, default_value",
        [
            # Test direct parameters
            ("v2", "category", "Walls", None),
            ("v3", "category", "Walls", None),
            # Test nested parameters - using both internal and friendly names
            ("v2", "WALL_ATTR_WIDTH_PARAM", 300, None),
            ("v3", "Construction.Width", 300, None),
            # Test parameters with units
            ("v2", "CURVE_ELEM_LENGTH", 5300.000000000001, None),
            ("v3", "Instance Parameters.Dimensions.Length", 5300.000000000001, None),
            # Test non-existent parameters with a default value
            ("v2", "parameters.non_existent", "default", "default"),
            ("v3", "properties.Parameters.non_existent", "default", "default"),
        ],
    )
    def test_parameter_value_retrieval(self, test_objects, obj_version, param_name, expected_value, default_value):
        """Test parameter value retrieval from both v2 and v3 objects."""
        v2_obj, v3_obj = test_objects
        obj = v2_obj if obj_version == "v2" else v3_obj
        result = PropertyRules.get_parameter_value(obj, param_name, default_value=default_value)
        assert result == expected_value

    @pytest.mark.parametrize(
        "param_name, expected_value, expected_result",
        [
            ("category", "Walls", True),  # Test exact match
            ("WALL_ATTR_WIDTH_PARAM", 300, True),  # Test numeric match
            ("category", "Windows", False),  # Test non-match
        ],
    )
    def test_v2_parameter_value_matching(self, test_objects, param_name, expected_value, expected_result):
        """Test parameter value matching in v2 objects."""
        v2_obj, _ = test_objects
        assert PropertyRules.is_parameter_value(v2_obj, param_name, expected_value) == expected_result

    @pytest.mark.parametrize(
        "param_name, expected_value, expected_result",
        [
            ("category", "Walls", True),  # Test exact match
            ("Width", 300, True),  # Test numeric match
            ("category", "Windows", False),  # Test non-match
        ],
    )
    def test_v3_parameter_value_matching(self, test_objects, param_name, expected_value, expected_result):
        """Test parameter value matching in v3 objects."""
        _, v3_obj = test_objects
        assert PropertyRules.is_parameter_value(v3_obj, param_name, expected_value) == expected_result

    @pytest.mark.parametrize(
        "comparison_func, param_name, value, expected_result",
        [
            (PropertyRules.is_parameter_value_greater_than, "WALL_ATTR_WIDTH_PARAM", "200", True),  # Test greater than
            (PropertyRules.is_parameter_value_less_than, "WALL_ATTR_WIDTH_PARAM", "400", True),  # Test less than
            (PropertyRules.is_parameter_value_in_range, "WALL_ATTR_WIDTH_PARAM", "200,400", True),  # Test in range
        ],
    )
    def test_v2_parameter_numeric_comparisons(self, test_objects, comparison_func, param_name, value, expected_result):
        """Test numeric parameter comparisons in v2 objects."""
        v2_obj, _ = test_objects
        assert comparison_func(v2_obj, param_name, value) == expected_result

    @pytest.mark.parametrize(
        "comparison_func, param_name, value, expected_result",
        [
            (PropertyRules.is_parameter_value_greater_than, "Width", "200", True),  # Test greater than
            (PropertyRules.is_parameter_value_less_than, "Width", "400", True),  # Test less than
            (PropertyRules.is_parameter_value_in_range, "Width", "200,400", True),  # Test in range
        ],
    )
    def test_v3_parameter_numeric_comparisons(self, test_objects, comparison_func, param_name, value, expected_result):
        """Test numeric parameter comparisons in v3 objects."""
        _, v3_obj = test_objects
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
    def test_v2_parameter_value_like(self, test_objects, param_name, pattern, fuzzy, expected_result):
        """Test pattern matching on parameter values in v2 objects."""
        v2_obj, _ = test_objects
        assert PropertyRules.is_parameter_value_like(v2_obj, param_name, pattern, fuzzy=fuzzy) == expected_result

    @pytest.mark.parametrize(
        "param_name, pattern, fuzzy, expected_result",
        [
            ("category", "^Walls$", False, True),  # Test exact pattern matches
            ("category", "Walls", True, True),  # Test fuzzy matches
            ("category", "Wall", False, True),  # Test partial pattern matches
            ("category", "^Windows$", False, False),  # Test non-matches
        ],
    )
    def test_v3_parameter_value_like(self, test_objects, param_name, pattern, fuzzy, expected_result):
        """Test pattern matching on parameter values in v3 objects."""
        _, v3_obj = test_objects
        assert PropertyRules.is_parameter_value_like(v3_obj, param_name, pattern, fuzzy=fuzzy) == expected_result

    @pytest.mark.parametrize(
        "param_name, valid_list, expected_result",
        [
            ("category", ["Walls", "Windows", "Doors"], True),  # Test value in list
            ("category", "Walls,Windows,Doors", True),  # Test comma-separated string list
            ("category", ["Windows", "Doors"], False),  # Test value not in list
        ],
    )
    def test_v2_parameter_lists(self, test_objects, param_name, valid_list, expected_result):
        """Test list-based parameter checks in v2 objects."""
        v2_obj, _ = test_objects
        assert PropertyRules.is_parameter_value_in_list(v2_obj, param_name, valid_list) == expected_result

    @pytest.mark.parametrize(
        "param_name, valid_list, expected_result",
        [
            ("category", ["Walls", "Windows", "Doors"], True),  # Test value in list
            ("category", "Walls,Windows,Doors", True),  # Test comma-separated string list
            ("category", ["Windows", "Doors"], False),  # Test value not in list
        ],
    )
    def test_v3_parameter_lists(self, test_objects, param_name, valid_list, expected_result):
        """Test list-based parameter checks in v3 objects."""
        _, v3_obj = test_objects
        assert PropertyRules.is_parameter_value_in_list(v3_obj, param_name, valid_list) == expected_result

    @pytest.mark.parametrize(
        "param_name, expected_result",
        [
            ("WALL_ATTR_ROOM_BOUNDING.value", True),  # Test true values
            ("wall_top_is_attached", False),  # Test false values
        ],
    )
    def test_v2_boolean_parameters(self, test_objects, param_name, expected_result):
        """Test boolean parameter checks in v2 objects."""
        v2_obj, _ = test_objects
        if expected_result:
            assert PropertyRules.is_parameter_value_true(v2_obj, param_name)
        else:
            assert PropertyRules.is_parameter_value_false(v2_obj, param_name)

    @pytest.mark.parametrize(
        "param_name, expected_result",
        [
            ("Room Bounding", True),  # Test true values
            ("top is attached", False),  # Test false values
            ("Top is Attached", False),  # Case sensitivity test
        ],
    )
    def test_v3_boolean_parameters(self, test_objects, param_name, expected_result):
        """Test boolean parameter checks in v3 objects."""
        _, v3_obj = test_objects
        if expected_result:
            assert PropertyRules.is_parameter_value_true(v3_obj, param_name)
        else:
            assert PropertyRules.is_parameter_value_false(v3_obj, param_name)

    @pytest.mark.parametrize(
        "param_name, expected_value, expected_result",
        [
            # Test numeric value comparisons
            ("WALL_ATTR_WIDTH_PARAM", 300, True),
            ("WALL_ATTR_WIDTH_PARAM.value", 300, True),
            ("baseLine.length", 5300.000000000002, True),
            # Test string value comparisons
            ("STRUCTURAL_MATERIAL_PARAM.value", "Fc24", True),
            ("ee1f33e1-5506-4a64-b87b-7b98d30aea52.value", "W30", True),
            # Test non-matches
            ("WALL_ATTR_WIDTH_PARAM", 301, False),
            ("nonexistent_param", "any_value", False),
        ],
    )
    def test_v2_parameter_value_comparisons(self, v2_wall, param_name, expected_value, expected_result):
        """Test value comparisons using v2 wall parameters."""
        assert PropertyRules.is_equal_value(v2_wall, param_name, expected_value) == expected_result

    @pytest.mark.parametrize(
        "attribute, value, expected",
        [
            # Test numeric value comparisons
            ("Type Parameters.Structure.Fc24 (0).thickness", 300, True),
            ("location.length", 5300.000000000002, True),
            ("location.length", 5300, True),
            # Test string value comparisons
            ("Type Parameters.Text.符号.value", "W30", True),
            ("Instance Parameters.Structural.Structural.value", "Yes", True),
            # Test non-matches
            ("Type Parameters.Structure.Fc24 (0).thickness", 301, False),
            ("nonexistent_param", "any_value", False),
        ],
    )
    def test_v3_parameter_value_comparisons(self, v3_wall, attribute, value, expected):
        """Test value comparisons using v3 wall parameters."""
        assert PropertyRules.is_equal_value(v3_wall, attribute, value) == expected

    @pytest.mark.parametrize(
        "wall, attribute, value, expected",
        [
            # V2 wall tests
            ("v2_wall", "WALL_ATTR_WIDTH_PARAM.value", 300, True),
            ("v2_wall", "type", "W30(Fc24)", True),
            ("v2_wall", "WALL_ATTR_WIDTH_PARAM.value", 300.0001, False),
            # V3 wall tests
            ("v3_wall", "Type Parameters.Structure.Fc24 (0).thickness", 300, True),
            ("v3_wall", "type", "W30(Fc24)", True),
            ("v3_wall", "Type Parameters.Structure.Fc24 (0).thickness", 300.0001, False),
            ("v3_wall", "location.length", 5300.000000000002, True),
            ("v3_wall", "location.length", 5300, False),
        ],
    )
    def test_identical_comparisons(self, request, wall, attribute, value, expected):
        """Test identical value comparisons on both wall versions."""
        wall_instance = request.getfixturevalue(wall)
        assert PropertyRules.is_identical_value(wall_instance, attribute, value) == expected

    @pytest.mark.parametrize(
        "wall, attribute, value",
        [
            # V2 wall tests
            ("v2_wall", "WALL_ATTR_WIDTH_PARAM.value", 301),
            ("v2_wall", "STRUCTURAL_MATERIAL_PARAM.value", "Fc25"),
            ("v2_wall", "nonexistent_param", "any_value"),
            # V3 wall tests
            ("v3_wall", "Type Parameters.Structure.Fc24 (0).thickness", 301),
            ("v3_wall", "Type Parameters.Text.符号.value", "W31"),
            ("v3_wall", "nonexistent_param", "any_value"),
        ],
    )
    def test_not_equal_comparisons(self, request, wall, attribute, value):
        """Test not equal comparisons on both wall versions."""
        wall_instance = request.getfixturevalue(wall)
        assert PropertyRules.is_not_equal_value(wall_instance, attribute, value)

    @pytest.mark.parametrize(
        "attribute, value, expected_equal, expected_identical",
        [
            # Test Yes/No conversion in equals (should convert)
            ("Instance Parameters.Structural.Structural.value", True, True, False),  # Yes vs True
            ("Instance Parameters.Structural.Structural.value", "Yes", True, True),  # Yes vs "Yes"
            ("Instance Parameters.Structural.Structural.value", "yes", True, False),  # Yes vs "yes"
        ],
    )
    def test_boolean_conversions(self, v3_wall, attribute, value, expected_equal, expected_identical):
        """Test conversion of Yes/No strings to boolean values."""
        assert PropertyRules.is_equal_value(v3_wall, attribute, value) == expected_equal
        assert PropertyRules.is_identical_value(v3_wall, attribute, value) == expected_identical

    @pytest.mark.parametrize(
        "wall, attribute, expected_value",
        [
            # V2 wall tests
            ("v2_wall", "WALL_ATTR_WIDTH_PARAM.value", "300"),
            ("v2_wall", "baseLine.length", "5300.000000000002"),
            # V3 wall tests
            ("v3_wall", "Type Parameters.Structure.Fc24 (0).thickness", "300"),
            ("v3_wall", "location.length", "5300.000000000002"),
        ],
    )
    def test_numeric_string_handling(self, wall, attribute, expected_value, request):
        """Test handling of numeric strings in both wall versions."""
        wall_instance = request.getfixturevalue(wall)  # Retrieve fixture dynamically
        assert PropertyRules.is_equal_value(wall_instance, attribute, expected_value)

    @pytest.mark.parametrize(
        "param_name, substring, expected_result",
        [
            ("speckle_type", "Revit", True),  # Test basic substring match
            ("speckle_type", "revit", True),  # Test case-insensitive
            ("speckle_type", "NotPresent", False),  # Test no match
            ("speckle_type", "", True),  # Test empty string
            ("non_existent", "anything", False),  # Test non-existent parameter
        ],
    )
    def test_parameter_value_contains(self, test_objects, param_name, substring, expected_result):
        """Test substring matching on parameter values."""
        v2_obj, _ = test_objects
        assert PropertyRules.is_parameter_value_containing(v2_obj, param_name, substring) == expected_result

    @pytest.mark.parametrize(
        "param_name, substring, expected_result",
        [
            ("speckle_type", "Revit", False),  # Should fail as it does contain Revit
            ("speckle_type", "NotPresent", True),  # Should pass as it doesn't contain
            ("speckle_type", "", False),  # Should fail as empty string is contained
            ("non_existent", "anything", True),  # Should pass as non-existent can't contain
        ],
    )
    def test_parameter_value_not_contains(self, test_objects, param_name, substring, expected_result):
        """Test negative substring matching on parameter values."""
        v2_obj, _ = test_objects
        assert PropertyRules.is_parameter_value_not_containing(v2_obj, param_name, substring) == expected_result

    @pytest.mark.parametrize(
        "param_name, expected_result",
        [
            ("category", True),  # Parameter exists with non-empty value
            ("family", True),  # Parameter exists with non-empty value
            ("non_existent_param", False),  # Parameter doesn't exist
            # The following would require setup with empty values
            # ("empty_string_param", False),  # Parameter exists but has empty string value
            # ("none_string_param", False),  # Parameter exists but has "None" string value
        ],
    )
    def test_parameter_not_empty(self, test_objects, param_name, expected_result):
        """Test 'not empty' check on parameter values."""
        v2_obj, _ = test_objects

        assert PropertyRules.is_parameter_value_not_empty(v2_obj, param_name) == expected_result
