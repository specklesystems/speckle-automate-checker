# Speckle Checker

Speckle Checker is an Automate function that validates Speckle objects against configurable rules defined in a
spreadsheet. This approach provides a flexible way to implement quality checks without coding, making it accessible to
all team members.

## Overview

The Checker function allows you to:

- Define validation rules in a spreadsheet
- Configure severity levels for issues
- Check properties across different types of objects
- Generate reports of validation results
- Apply consistent standards across projects

## Getting Started

### 1. Prepare Your Rule Spreadsheet

1. Access the [template spreadsheet](https://docs.google.com/spreadsheets/d/1hiPSw23eOaqd27QD_YsXvZg9PWm7_XBx/edit) (
   make a copy to your drive)
2. Define your rules using the format explained below
3. Publish your rules by clicking "File > Download > Tab-separated values (.tsv)"
4. Upload the TSV file to a hosting service (Google Drive, Dropbox, etc.) and get a public URL

### 2. Create an Automation

1. Go to [Speckle Automate](https://automate.speckle.dev/)
2. Create a new Automation
3. Select the Checker function
4. Configure the function:
    - Paste your TSV URL
    - Set minimum severity level to report
    - Configure other options as needed
5. Save and run your automation

## Rule Definition Format

Rules are defined in a spreadsheet with the following columns:

| Rule Number | Logic | Property Name | Predicate    | Value     | Message              | Report Severity |
|-------------|-------|---------------|--------------|-----------|----------------------|-----------------|
| 1           | WHERE | category      | matches      | Walls     | Wall thickness check | ERROR           |
| 1           | AND   | Width         | greater than | 200       |                      |                 |
| 2           | WHERE | category      | matches      | Columns   | Column height check  | WARNING         |
| 2           | AND   | height        | in range     | 2500,4000 |                      |                 |

### Column Explanation

- **Rule Number**: Groups conditions that belong to the same rule
- **Logic**: Defines how conditions are combined (WHERE, AND, CHECK)
- **Property Name**: The object property or parameter to check
- **Predicate**: Comparison operation (equals, greater than, etc.)
- **Value**: Reference value for comparison
- **Message**: Description shown in validation results
- **Report Severity**: ERROR, WARNING, or INFO

### Supported Predicates

| Predicate        | Description                 | Example                            |
|------------------|-----------------------------|------------------------------------|
| exists           | Checks if a property exists | `height` exists                    |
| equal to         | Exact value match           | `width` equal to `300`             |
| not equal to     | Value doesn't match         | `material` not equal to `Concrete` |
| greater than     | Value exceeds threshold     | `height` greater than `3000`       |
| less than        | Value below threshold       | `thickness` less than `50`         |
| in range         | Value within bounds         | `elevation` in range `0,10000`     |
| in list          | Value in allowed set        | `type` in list `W1,W2,W3`          |
| contains         | Property contains substring | `name` contains `Beam`             |
| does not contain | Property doesn't contain    | `name` does not contain `temp`     |
| is true          | Boolean property is true    | `is_structural` is true            |
| is false         | Boolean property is false   | `is_placeholder` is false          |
| is like          | Pattern matching            | `name` is like `^BR\d+$`           |

## Rule Logic

- **WHERE**: Filters objects to check (like SELECT WHERE in SQL)
- **AND**: Additional filter conditions
- **CHECK**: Final check condition (optional, defaults to last AND)

Objects pass a rule when they match all conditions. Objects that match WHERE/AND filters but fail the CHECK condition
are reported as issues.

## Working with Object Properties

The Checker understands properties in Speckle objects regardless of schema:

- Direct properties: `category`, `name`, `id`
- Nested properties: `parameters.WIDTH.value`
- Revit parameters: Use parameter names like `Mark`, `Width`, `Assembly Code`

## Example Rules

### Wall Thickness Check

```
Rule 1: WHERE category equals "Walls" AND width less than "200"
Message: "Wall too thin - minimum thickness is 200mm"
Severity: ERROR
```

### Door Naming Convention

```
Rule 2: WHERE category equals "Doors" AND name is not like "^D\d{3}$"
Message: "Door name must follow pattern D followed by 3 digits"
Severity: WARNING
```

### Structural Column Height Range

```
Rule 3: WHERE category equals "Columns" AND is_structural is true AND height not in range "2400,4000"
Message: "Structural column height outside acceptable range (2400-4000mm)"
Severity: ERROR
```

## Support

For issues or questions, please open a GitHub issue or contact your Speckle support representative.