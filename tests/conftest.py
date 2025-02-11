import pytest
from specklepy.objects.base import Base


@pytest.fixture
def v2_wall():
    """Creates a v2-style Speckle wall object."""
    wall = Base()
    wall.id = "cdb18060dc48281909e94f0f1d8d3cc0"
    wall.type = "W30(Fc24)"
    wall.units = "mm"
    wall.family = "Basic Wall"
    wall.height = 1400
    wall.flipped = False
    wall.category = "Walls"
    wall.elementId = "4479852"
    wall.worksetId = "0"
    wall.structural = True
    wall.baseOffset = -2000
    wall.topOffset = -600

    # Create base line geometry
    wall.baseLine = Base()
    wall.baseLine.start = Base()
    wall.baseLine.start.x = 22400.000000000007
    wall.baseLine.start.y = 15199.999999999998
    wall.baseLine.start.z = -2000.0000000000002
    wall.baseLine.end = Base()
    wall.baseLine.end.x = 22400.000000000015
    wall.baseLine.end.y = 20500
    wall.baseLine.end.z = -2000.0000000000002
    wall.baseLine.units = "mm"
    wall.baseLine.length = 5300.000000000002

    # Create parameters structure
    wall.parameters = Base()

    # Standard parameter
    wall.parameters["WALL_ATTR_WIDTH_PARAM"] = Base()
    wall.parameters["WALL_ATTR_WIDTH_PARAM"].name = "Width"
    wall.parameters["WALL_ATTR_WIDTH_PARAM"].value = 300
    wall.parameters["WALL_ATTR_WIDTH_PARAM"].units = "mm"

    # Parameter with GUID key
    wall.parameters["ee1f33e1-5506-4a64-b87b-7b98d30aea52"] = Base()
    wall.parameters["ee1f33e1-5506-4a64-b87b-7b98d30aea52"].name = "符号"
    wall.parameters["ee1f33e1-5506-4a64-b87b-7b98d30aea52"].value = "W30"
    wall.parameters["ee1f33e1-5506-4a64-b87b-7b98d30aea52"].isShared = True
    wall.parameters[
        "ee1f33e1-5506-4a64-b87b-7b98d30aea52"
    ].internalDefinitionName = "ee1f33e1-5506-4a64-b87b-7b98d30aea52"

    wall.parameters["STRUCTURAL_MATERIAL_PARAM"] = Base()
    wall.parameters["STRUCTURAL_MATERIAL_PARAM"].name = "Structural Material"
    wall.parameters["STRUCTURAL_MATERIAL_PARAM"].value = "Fc24"

    # Create basic level reference
    wall.level = Base()
    wall.level.name = "1FL"
    wall.level.elevation = 0
    wall.level.units = "mm"

    return wall


@pytest.fixture
def v3_wall():
    """Creates a v3-style Speckle wall object."""
    wall = Base()
    wall.id = "46f06fef727d64a0bbcbd7ced51e0cd2"
    wall.name = "Walls - W30(Fc24)"
    wall.type = "W30(Fc24)"
    wall.units = "mm"
    wall.family = "Basic Wall"
    wall.flipped = False
    wall.category = "Walls"
    wall.elementId = "4479852"
    wall.worksetId = "0"

    # Create location geometry
    wall.location = Base()
    wall.location.start = Base()
    wall.location.start.x = 22400.000000000007
    wall.location.start.y = 15199.999999999998
    wall.location.start.z = 0
    wall.location.end = Base()
    wall.location.end.x = 22400.000000000015
    wall.location.end.y = 20500
    wall.location.end.z = 0
    wall.location.units = "mm"
    wall.location.length = 5300.000000000002

    # Create nested properties structure
    wall.properties = Base()
    wall.properties.Parameters = Base()

    # Type Parameters
    wall.properties.Parameters["Type Parameters"] = Base()

    # Add Text section with GUID parameter
    wall.properties.Parameters["Type Parameters"].Text = Base()
    wall.properties.Parameters["Type Parameters"].Text["符号"] = {
        "name": "符号",
        "value": "W30",
        "internalDefinitionName": "ee1f33e1-5506-4a64-b87b-7b98d30aea52",
    }

    wall.properties.Parameters["Type Parameters"].Structure = Base()
    wall.properties.Parameters["Type Parameters"].Structure["Fc24 (0)"] = {
        "units": "mm",
        "function": "Structure",
        "material": "Fc24",
        "thickness": 300,
    }

    # Instance Parameters
    wall.properties.Parameters["Instance Parameters"] = Base()
    wall.properties.Parameters["Instance Parameters"].Structural = Base()
    wall.properties.Parameters["Instance Parameters"].Structural.Structural = {"name": "Structural", "value": "Yes"}

    # Create basic level references
    wall.level = Base()
    wall.level.name = "1FL"
    wall.level.elevation = 0
    wall.level.units = "mm"

    wall.topLevel = Base()
    wall.topLevel.name = "1FL"
    wall.topLevel.elevation = 0
    wall.topLevel.units = "mm"

    return wall
