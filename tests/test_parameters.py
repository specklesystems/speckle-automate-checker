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


def load_test_objects(v2_wall: Any, v3_wall: Any) -> tuple[Base, Base]:
    """Load test objects from a Speckle server."""
    client = SpeckleClient(host="https://app.speckle.systems", use_ssl=True)

    load_dotenv(dotenv_path="../.env")

    client.authenticate_with_token(os.getenv("SPECKLE_TOKEN"))

    transport = ServerTransport(client=client, stream_id=os.getenv("SPECKLE_PROJECT_ID"))

    speckle_print(v2_wall)
    v2_obj = operations.receive("cdb18060dc48281909e94f0f1d8d3cc0", transport)
    v3_obj = operations.receive("46f06fef727d64a0bbcbd7ced51e0cd2", transport)

    return v2_wall, v3_wall


@pytest.fixture
def test_objects(v2_wall: Any, v3_wall: Any) -> tuple[Base, Base]:
    """Pytest fixture to provide test objects."""
    return load_test_objects(v2_wall, v3_wall)


def test_deserialization_structure(test_objects):
    """Test that objects are properly deserialized with correct structure."""
    v2_obj, v3_obj = test_objects

    # Test basic object properties
    assert isinstance(v2_obj, Base)
    assert isinstance(v3_obj, Base)

    # Test v2 structure
    assert hasattr(v2_obj, "parameters")
    assert v2_obj["parameters"] is not None

    # Test v3 structure
    assert hasattr(v3_obj, "properties")
    assert v3_obj["properties"] is not None
    assert "Parameters" in v3_obj["properties"].get_member_names()


def test_v2_parameter_exists(test_objects):
    """Test parameter existence checking in both v2 and v3 objects."""
    v2_obj, _ = test_objects

    # Test parameters that should exist in both
    assert PropertyRules.has_parameter(v2_obj, "category")

    # Test nested parameters
    assert PropertyRules.has_parameter(v2_obj, "WALL_ATTR_WIDTH_PARAM")
    assert PropertyRules.has_parameter(v2_obj, "WALL_ATTR_WIDTH_PARAM.value")

    assert PropertyRules.get_parameter_value(v2_obj, "WALL_ATTR_WIDTH_PARAM.id")
    assert PropertyRules.get_parameter_value(v2_obj, "WALL_ATTR_WIDTH_PARAM.value")
    assert PropertyRules.get_parameter_value(v2_obj, "WALL_ATTR_WIDTH_PARAM")
    assert PropertyRules.get_parameter_value(v2_obj, "WALL_ATTR_WIDTH_PARAM.units")

    # Test non-existent parameters
    assert not PropertyRules.has_parameter(v2_obj, "non_existent_param")


def test_v3_parameter_exists(test_objects):
    """Test parameter existence checking in both v2 and v3 objects."""
    _, v3_obj = test_objects

    # Test parameters that should exist in both
    assert PropertyRules.has_parameter(v3_obj, "category")

    # Test nested parameters
    assert PropertyRules.has_parameter(v3_obj, "Width")

    # Test non-existent parameters
    assert not PropertyRules.has_parameter(v3_obj, "non_existent_param")


def test_v3_parameter_search_equivalence(test_objects):
    """Test parameter existence checking in both v2 and v3 objects."""
    _, v3_obj = test_objects

    assert PropertyRules.get_parameter_value(
        v3_obj, "properties.Parameters.Instance Parameters.Dimensions.Length.value"
    ) == PropertyRules.get_parameter_value(v3_obj, "Instance Parameters.Dimensions.Length")


def test_parameter_value_retrieval(test_objects):
    """Test parameter value retrieval from both v2 and v3 objects."""
    v2_obj, v3_obj = test_objects

    # Test direct parameters
    assert PropertyRules.get_parameter_value(v2_obj, "category") == "Walls"
    assert PropertyRules.get_parameter_value(v3_obj, "category") == "Walls"

    # Test nested parameters - using both internal and friendly names
    # For v2: parameters > WALL_ATTR_WIDTH_PARAM > value
    # For v3: properties > Parameters > Type Parameters > Construction > Width > value
    assert PropertyRules.get_parameter_value(v2_obj, "WALL_ATTR_WIDTH_PARAM") == 300
    assert PropertyRules.get_parameter_value(v3_obj, "Construction.Width") == 300

    # Test parameters with units
    # For v2: parameters > CURVE_ELEM_LENGTH > value
    # For v3: properties > Parameters > Instance Parameters > Dimensions > Length > value
    assert PropertyRules.get_parameter_value(v2_obj, "CURVE_ELEM_LENGTH") == 5300.000000000001
    assert PropertyRules.get_parameter_value(v3_obj, "Instance Parameters.Dimensions.Length") == 5300.000000000001

    # Test non-existent parameters
    # Use strict mode to avoid partial matches
    assert PropertyRules.get_parameter_value(v2_obj, "parameters.non_existent", default_value="default") == "default"
    assert (
        PropertyRules.get_parameter_value(v3_obj, "properties.Parameters.non_existent", default_value="default")
        == "default"
    )


def test_v2_parameter_value_matching(test_objects):
    """Test parameter value matching in both v2 and v3 objects."""
    v2_obj, _ = test_objects

    # Test exact matches
    assert PropertyRules.is_parameter_value(v2_obj, "category", "Walls")

    # Test numeric matches
    assert PropertyRules.is_parameter_value(v2_obj, "WALL_ATTR_WIDTH_PARAM", 300)

    # Test non-matches
    assert not PropertyRules.is_parameter_value(v2_obj, "category", "Windows")


def test_v3_parameter_value_matching(test_objects):
    """Test parameter value matching in both v2 and v3 objects."""
    _, v3_obj = test_objects

    # Test exact matches
    assert PropertyRules.is_parameter_value(v3_obj, "category", "Walls")

    # Test numeric matches
    assert PropertyRules.is_parameter_value(v3_obj, "Width", 300)

    # Test non-matches
    assert not PropertyRules.is_parameter_value(v3_obj, "category", "Windows")


def test_v2_parameter_numeric_comparisons(test_objects):
    """Test numeric parameter comparisons in both v2 and v3 objects."""
    v2_obj, _ = test_objects

    # Test greater than
    assert PropertyRules.is_parameter_value_greater_than(v2_obj, "WALL_ATTR_WIDTH_PARAM", "200")

    # Test less than
    assert PropertyRules.is_parameter_value_less_than(v2_obj, "WALL_ATTR_WIDTH_PARAM", "400")

    # Test in range
    assert PropertyRules.is_parameter_value_in_range(v2_obj, "WALL_ATTR_WIDTH_PARAM", "200,400")


def test_v3_parameter_numeric_comparisons(test_objects):
    """Test numeric parameter comparisons in both v2 and v3 objects."""
    _, v3_obj = test_objects

    # Test greater than
    assert PropertyRules.is_parameter_value_greater_than(v3_obj, "Width", "200")

    # Test less than
    assert PropertyRules.is_parameter_value_less_than(v3_obj, "Width", "400")

    # Test in range
    assert PropertyRules.is_parameter_value_in_range(v3_obj, "Width", "200,400")


def test_v2_parameter_value_like(test_objects):
    """Test pattern matching on parameter values in both v2 and v3 objects."""
    v2_obj, _ = test_objects

    # Test exact pattern matches
    assert PropertyRules.is_parameter_value_like(v2_obj, "category", "^Walls$")

    # Test fuzzy matches
    assert PropertyRules.is_parameter_value_like(v2_obj, "category", "Walls", fuzzy=True)

    # Test partial pattern matches
    assert PropertyRules.is_parameter_value_like(v2_obj, "category", "Wall")

    # Test non-matches
    assert not PropertyRules.is_parameter_value_like(v2_obj, "category", "^Windows$")


def test_v3_parameter_value_like(test_objects):
    """Test pattern matching on parameter values in both v2 and v3 objects."""
    _, v3_obj = test_objects

    # Test exact pattern matches
    assert PropertyRules.is_parameter_value_like(v3_obj, "category", "^Walls$")

    # Test fuzzy matches
    assert PropertyRules.is_parameter_value_like(v3_obj, "category", "Walls", fuzzy=True)

    # Test partial pattern matches
    assert PropertyRules.is_parameter_value_like(v3_obj, "category", "Wall")

    # Test non-matches
    assert not PropertyRules.is_parameter_value_like(v3_obj, "category", "^Windows$")


def test_v2_parameter_lists(test_objects):
    """Test list-based parameter checks in both v2 and v3 objects."""
    v2_obj, _ = test_objects

    valid_categories = ["Walls", "Windows", "Doors"]

    # Test value in list
    assert PropertyRules.is_parameter_value_in_list(v2_obj, "category", valid_categories)

    # Test comma-separated string list
    assert PropertyRules.is_parameter_value_in_list(v2_obj, "category", "Walls,Windows,Doors")

    # Test value not in list
    invalid_categories = ["Windows", "Doors"]
    assert not PropertyRules.is_parameter_value_in_list(v2_obj, "category", invalid_categories)


def test_v3_parameter_lists(test_objects):
    """Test list-based parameter checks in both v2 and v3 objects."""
    _, v3_obj = test_objects

    valid_categories = ["Walls", "Windows", "Doors"]

    # Test value in list
    assert PropertyRules.is_parameter_value_in_list(v3_obj, "category", valid_categories)

    # Test comma-separated string list
    assert PropertyRules.is_parameter_value_in_list(v3_obj, "category", "Walls,Windows,Doors")

    # Test value not in list
    invalid_categories = ["Windows", "Doors"]
    assert not PropertyRules.is_parameter_value_in_list(v3_obj, "category", invalid_categories)


def test_v2_boolean_parameters(test_objects):
    """Test boolean parameter checks in both v2 and v3 objects."""
    v2_obj, _ = test_objects

    # Test true values
    assert PropertyRules.is_parameter_value_true(v2_obj, "WALL_ATTR_ROOM_BOUNDING.value")

    # Test false values
    assert PropertyRules.is_parameter_value_false(v2_obj, "wall_top_is_attached")


def test_v3_boolean_parameters(test_objects):
    """Test boolean parameter checks in both v2 and v3 objects."""
    _, v3_obj = test_objects

    # Test true values
    assert PropertyRules.is_parameter_value_true(v3_obj, "Room Bounding")

    # Test false values
    assert PropertyRules.is_parameter_value_false(v3_obj, "top is attached")
    assert PropertyRules.is_parameter_value_false(v3_obj, "Top is Attached")
