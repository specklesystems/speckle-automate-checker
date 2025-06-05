import pytest
from specklepy.objects.base import Base


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
    wall.location.id = "9c76b8de34382c9052965ee463f8374b"
    wall.location.start = Base()
    wall.location.start.x = 22400.000000000007
    wall.location.start.y = 15199.999999999998
    wall.location.start.z = 0
    wall.location.start.id = "d0c4fdb2e11cc825e7f05f9dc88a0be1"
    wall.location.start.units = "mm"
    wall.location.start.speckle_type = "Objects.Geometry.Point"
    wall.location.end = Base()
    wall.location.end.x = 22400.000000000015
    wall.location.end.y = 20500
    wall.location.end.z = 0
    wall.location.end.id = "3455575bfd8939f264d295b61e74156f"
    wall.location.end.units = "mm"
    wall.location.end.speckle_type = "Objects.Geometry.Point"
    wall.location.units = "mm"
    wall.location.domain = Base()
    wall.location.domain.id = "3b97feaad2dbcc2d894c9cec024a9bf2"
    wall.location.domain.end = 17.388451443569522
    wall.location.domain.start = -3.552713668866051e-14
    wall.location.domain.speckle_type = "Objects.Primitive.Interval"
    wall.location.length = 5300.000000000002
    wall.location.speckle_type = "Objects.Geometry.Line"

    # Create level references
    wall.level = Base()
    wall.level.name = "1FL"
    wall.level.units = "mm"
    wall.level.elevation = 0

    wall.topLevel = Base()
    wall.topLevel.name = "1FL"
    wall.topLevel.units = "mm"
    wall.topLevel.elevation = 0

    # Create properties structure
    wall.properties = Base()
    wall.properties.Parameters = Base()
    wall.properties.Parameters["Type Parameters"] = Base()

    # Add Text section
    wall.properties.Parameters["Type Parameters"].Text = Base()
    wall.properties.Parameters["Type Parameters"].Text["符号"] = {
        "name": "符号",
        "value": "W30",
        "internalDefinitionName": "ee1f33e1-5506-4a64-b87b-7b98d30aea52",
    }

    # Add Structure section
    wall.properties.Parameters["Type Parameters"].Structure = Base()
    wall.properties.Parameters["Type Parameters"].Structure["Fc24 (0)"] = {
        "units": "mm",
        "function": "Structure",
        "material": "Fc24",
        "thickness": 300,
    }

    # Add Construction section
    wall.properties.Parameters["Type Parameters"].Construction = Base()
    wall.properties.Parameters["Type Parameters"].Construction.Width = {
        "name": "Width",
        "units": "Millimeters",
        "value": 300,
        "internalDefinitionName": "WALL_ATTR_WIDTH_PARAM",
    }

    # Add Instance Parameters
    wall.properties.Parameters["Instance Parameters"] = Base()
    wall.properties.Parameters["Instance Parameters"].Structural = Base()
    wall.properties.Parameters["Instance Parameters"].Structural.Structural = {
        "name": "Structural",
        "value": "Yes",
    }

    return wall
