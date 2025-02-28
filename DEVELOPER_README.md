# Checker Function Developer Guide

This document provides technical details for developers working on the Speckle Checker Automate function.

## Project Overview

The Checker function enables validation of Speckle objects against user-defined rules in a spreadsheet. It's designed to
be flexible, supporting various object schemas including both v2 and v3 Speckle APIs.

## Setup Development Environment

### Prerequisites

- Python 3.10+
- Poetry for dependency management

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Activate the virtual environment:
   ```bash
   poetry shell
   ```

### Test Automation Environment

The project uses Speckle's [Test Automation feature](https://speckle.guide/automate/function-testing.html) to run
integration tests against real Speckle data. This provides a sandboxed environment to validate the function's business
logic without triggering actual automations.

#### Setting Up a Test Automation

1. Navigate to your Speckle project
2. Go to the **Automations** tab
3. Click **New Automation**
4. Select **Create Test Automation** in the bottom left
5. Follow the configuration steps

Note: To create a test automation, you must:

- Be an owner of the Speckle project
- Have published this function to the Function Library
- Have at least one release for the function

#### Environment Configuration

For local integration testing, create a `.env` file in the project root with these variables:

```
# Your Personal Access Token from Speckle
SPECKLE_TOKEN=your_speckle_token

# The Speckle server URL
SPECKLE_SERVER_URL=https://app.speckle.systems

# From the test automation URL: /projects/[project-id]/automations/[automation-id]
SPECKLE_PROJECT_ID=your_project_id
SPECKLE_AUTOMATION_ID=your_automation_id
```

This configuration allows the test suite to:

1. Connect to your test automation via the Speckle API
2. Run the function locally against real Speckle data
3. Submit results to the test automation for validation

For detailed instructions, refer to
the [official documentation on function testing](https://speckle.guide/automate/function-testing.html#how-to-create-a-test-automation).

#### Running Integration Tests

With the `.env` file configured:

```bash
# Run the integration tests
pytest test_function.py
```

The SDK utilities will automatically:

- Connect to your test automation
- Execute your function with the specified test data
- Submit results back to Speckle

Test results will be visible on the automation page in the Speckle UI.

#### Unit Tests

For unit tests that don't require a full Speckle connection, you can run:

```bash
# Run unit tests only
pytest test_comparisons.py test_rule_processing.py
```

Note: The `.env` file should never be committed to version control (it's included in .gitignore)

## Project Structure

```
├── main.py                  # Entry point for Automate
├── src/
│   ├── function.py          # Main function logic
│   ├── inputs.py            # Function input schema
│   ├── helpers.py           # Utility functions
│   ├── filters.py           # Object filtering functions
│   ├── rules.py             # Rule definitions and property handling
│   ├── predicates.py        # Predicate mapping for spreadsheet values
│   ├── rule_processor.py    # Rule application and result handling
│   └── spreadsheet.py       # TSV file parsing
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_function.py     # Main function tests
│   ├── test_comparisons.py  # Value comparison tests
│   ├── test_parameters.py   # Parameter handling tests
│   └── test_rule_processing.py  # Rule processing tests
├── pyproject.toml           # Project dependencies
└── poetry.lock              # Locked dependencies
```

## Core Components

### 1. Function Execution Flow

The main execution flow is defined in `function.py`:

1. `automate_function()` receives context and inputs from Automate
2. Retrieves Speckle objects via `automate_context.receive_version()`
3. Flattens the object tree using `flatten_base()`
4. Loads rules from the spreadsheet URL via `read_rules_from_spreadsheet()`
5. Applies rules to objects using `apply_rules_to_objects()`
6. Reports results via the Automate context

### 2. Rule Processing

Rules are processed through several stages:

1. **Spreadsheet Parsing** (`spreadsheet.py`):
    - Reads TSV data
    - Groups rules by rule number
    - Validates rule structure

2. **Rule Application** (`rule_processor.py`):
    - Processes rule logic (WHERE, AND, CHECK)
    - Evaluates conditions against objects
    - Attaches results to objects in Automate context

3. **Property Rules** (`rules.py`):
    - Handles property lookups in objects
    - Implements comparison logic
    - Supports both v2 and v3 Speckle schemas

### 3. Property Access System

The system uses a flexible property access mechanism that works with different Speckle schemas:

- **V2 Schema**: Properties in `parameters` dictionary with internal definition names
- **V3 Schema**: Properties in nested `properties.Parameters` structure

The `PropertyRules` class provides methods to:

- Find properties by path or name
- Extract values with appropriate type conversion
- Perform comparisons with tolerance and type handling

## Test-Driven Development for Rules

The test infrastructure is designed to support Test-Driven Development (TDD) when creating new rules or extending
functionality. This approach is especially powerful for rule development as it allows you to verify behavior against
known test objects.

### Using Test Fixtures for Rule Development

The `conftest.py` file contains test fixtures that provide sample Speckle objects for testing:

```python
@pytest.fixture
def v2_wall():
    """Creates a v2-style Speckle wall object"""
    wall = Base()
    wall.id = "cdb18060dc48281909e94f0f1d8d3cc0"
    wall.type = "W30(Fc24)"
    wall.units = "mm"
    wall.family = "Basic Wall"
    wall.height = 1400
    wall.flipped = False
    wall.category = "Walls"
    # ... more properties

    return wall


@pytest.fixture
def v3_wall():
    """Creates a v3-style Speckle wall object"""
    wall = Base()
    wall.id = "46f06fef727d64a0bbcbd7ced51e0cd2"
    wall.name = "Walls - W30(Fc24)"
    wall.type = "W30(Fc24)"
    wall.units = "mm"
    wall.family = "Basic Wall"
    # ... more properties

    return wall
```

These fixtures create standardized test objects that represent different Speckle schema versions, allowing you to test
rule behavior consistently.

### TDD Workflow for New Rules

When developing a new rule or predicate, follow this TDD approach:

1. **Add test fixtures**: First, expand `conftest.py` with representative objects that your rule will process

2. **Write tests first**: Create test cases in a test file (e.g., `test_my_rule.py`):
   ```python
   def test_new_wall_rule(v2_wall, v3_wall):
       """Test a new rule that checks wall thickness requirements"""
       # Test with v2 schema
       assert PropertyRules.is_new_wall_check(v2_wall, "width", "300")
       
       # Test with v3 schema
       assert PropertyRules.is_new_wall_check(v3_wall, "Width", "300")
       
       # Test failure case
       v2_wall.parameters["WALL_ATTR_WIDTH_PARAM"].value = 200
       assert not PropertyRules.is_new_wall_check(v2_wall, "width", "300")
   ```

3. **Implement the rule**: Add the new rule method to the `PropertyRules` class in `rules.py`:
   ```python
   @staticmethod
   def is_new_wall_check(speckle_object: Base, parameter_name: str, expected_value: str) -> bool:
       """Checks if a wall meets specific thickness requirements"""
       parameter_value = PropertyRules.get_parameter_value(speckle_object, parameter_name)
       # Implement rule logic
       return result
   ```

4. **Add to predicate mapping**: Register your new rule in `predicates.py`:
   ```python
   PREDICATE_METHOD_MAP = {
       # Existing predicates...
       "new_wall_check": PropertyRules.is_new_wall_check.__name__,
   }
   ```

5. **Run tests to verify**:
   ```bash
   pytest test_my_rule.py -v
   ```

### Creating Comprehensive Test Objects

For the most effective testing, your test objects in `conftest.py` should:

1. **Include diverse objects**: Walls, columns, beams, etc.
2. **Cover edge cases**: Null values, missing properties, special characters
3. **Represent both schemas**: Include both v2 and v3 format objects
4. **Include real-world examples**: Extract sample objects from actual projects

You can extract real objects for testing using:

```python
# Example code to extract and save real objects for test fixtures
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.transports.server import ServerTransport

client = SpeckleClient(host="app.speckle.systems")
client.authenticate_with_token(token)

transport = ServerTransport(client=client, stream_id="stream_id")
obj = operations.receive("object_id", transport)

# Print structure to help with fixture creation
print(obj.get_member_names())
print(obj.get_dynamic_member_names())
```

By following this TDD approach and maintaining comprehensive test fixtures, you can develop robust rules that work
reliably across different object schemas and handle edge cases appropriately.

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parameters.py

# Run with coverage
pytest --cov=src
```

### Test Data

Test fixtures in `conftest.py` provide sample objects:

- `v2_wall`: Wall object in v2 schema
- `v3_wall`: Wall object in v3 schema

### Manual Testing with Real Data

For testing with real Speckle data:

```python
from specklepy.api import operations
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.transports.server import ServerTransport

client = SpeckleClient(host="app.speckle.systems")
account = get_account_from_token(token, "app.speckle.systems")
client.authenticate_with_account(account)

transport = ServerTransport(client=client, stream_id="your_stream_id")
commit = client.commit.get(stream_id="your_stream_id", commit_id="your_commit_id")
obj = operations.receive(commit.referencedObject, transport)
```

## Deployment

The function is deployed through GitHub Actions:

1. Create a GitHub release to trigger the build workflow
2. The workflow builds the necessary artifacts and pushes them to the Speckle Automate registry
3. The function becomes available in the Speckle Automate UI

## Performance Considerations

- **Large Object Trees**: When processing large models, use aggressive filtering with WHERE clauses
- **Rule Complexity**: Minimize the number of nested property lookups
- **Memory Usage**: Be aware of object reference handling and avoid deep copies

## Troubleshooting

### Common Issues

1. **Rule not matching expected objects**:
    - Check property paths for the specific object type
    - Verify data types (strings vs. numbers)
    - Enable debug logging

2. **Slow performance**:
    - Check for inefficient property lookups
    - Add more specific WHERE filters to reduce object set

3. **Docker build failures**:
    - Check dependency compatibility
    - Verify Python version requirements

## Contributing

1. Create a branch for your feature or fix
2. Add tests for new functionality
3. Update documentation
4. Submit a pull request
5. Ensure CI tests pass

## Future Development

Potential improvements:

- Support for more complex rule logic (OR conditions)
- UI-based rule editor
- Result visualization tools
- Performance optimizations for large models
- Support for referencing other objects in rules