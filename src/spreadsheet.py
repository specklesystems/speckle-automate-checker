"""Module for reading and processing rules from a cloud hosted TSV file.

This module handles the loading and processing of validation rules from external
spreadsheet data, enabling non-technical users to define and modify rules.

Key features:
1. Reading from hosted TSV files (e.g., from Google Sheets)
2. Processing rule numbers for consistent grouping
3. Handling mixed data types in spreadsheet columns
4. Validating rule structure and providing feedback
5. Grouping related rule conditions for execution

The spreadsheet format used follows a specific structure:
- Rule Number: Groups related conditions together
- Logic: WHERE/AND/CHECK to define condition relationships
- Property Name: The property path to check
- Predicate: The comparison operation (equals, greater than, etc.)
- Value: The value to compare against
- Message: The message to display for rule results
- Severity: INFO/WARNING/ERROR level for failures
"""

import traceback

import pandas as pd
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy


def process_rule_numbers(df: DataFrame) -> DataFrame:
    """Process rule numbers in a DataFrame while preserving original rule identifiers.

    This function handles various rule numbering scenarios:
    1. Preserves existing rule numbers exactly as provided
    2. Generates sequential numbers for missing rule numbers
    3. Ensures all rows in a logical rule group have the same rule number

    This is important because rule numbers determine how conditions are grouped
    and executed together.

    Args:
        df: DataFrame with columns including 'Rule Number' and 'Logic'

    Returns:
        DataFrame with processed rule numbers, where all related conditions
        have the same rule number
    """
    # Create a copy to avoid modifying original
    df = df.copy()

    # Initialize tracking variables
    used_rule_nums = set()
    processed_rule_nums = []
    next_auto_num = 1  # For generating missing rule numbers only

    # Find indices where Logic is 'WHERE' to identify rule group starts
    where_indices = df[df["Logic"].str.upper() == "WHERE"].index

    # Process each group
    for i in range(len(where_indices)):
        start_idx = where_indices[i]
        end_idx = where_indices[i + 1] if i + 1 < len(where_indices) else len(df)

        # Get slice of rows for this group
        group_slice = df.iloc[start_idx:end_idx]

        # Try to get rule number from first row
        group_rule_num = group_slice["Rule Number"].iloc[0]

        if pd.isna(group_rule_num):
            # If no rule number, generate next available number
            while str(next_auto_num) in used_rule_nums:
                next_auto_num += 1
            group_rule_num = str(next_auto_num)
            next_auto_num += 1
        else:
            # Keep the original rule number exactly as is
            group_rule_num = str(group_rule_num)

        # Update tracking
        used_rule_nums.add(group_rule_num)

        # Fill rule numbers for this group
        processed_rule_nums.extend([group_rule_num] * len(group_slice))

    # Update DataFrame with processed rule numbers
    df["Rule Number"] = processed_rule_nums

    return df


def validate_rule_numbers(df: DataFrame) -> list[str]:
    """ "
    Validate rule numbers and return any warnings or errors.

    This checks for issues like:
    1. Missing rule numbers
    2. Non-integer rule numbers
    3. Duplicate rule numbers

    These validations help ensure rule integrity without being overly strict,
    allowing for different user approaches to rule numbering.

    Args:
        df: DataFrame with processed rule numbers

    Returns:
        List of warning/error messages
    """
    messages = []

    # Check for missing rule numbers
    if df["Rule Number"].isna().any():
        messages.append("Warning: Some rules are missing rule numbers")

    # # Check for non-integer rule numbers
    # non_int_mask = df["Rule Number"].apply(lambda x: not pd.isna(x) and not float(x).is_integer())
    # if non_int_mask.any():
    #     messages.append("Warning: Some rule numbers are not integers")

    # Check for duplicate rule numbers in WHERE rows
    where_rules = df[df["Logic"].str.upper() == "WHERE"]["Rule Number"]
    duplicates = where_rules[where_rules.duplicated()]
    if not duplicates.empty:
        messages.append(f"Warning: Duplicate rule numbers found: {list(duplicates)}")

    return messages


def read_rules_from_spreadsheet(url: str) -> tuple[DataFrameGroupBy, list[str]] | tuple[None, list[str]]:
    """ "
    Reads rules from a TSV file at the provided URL, processes them, and returns grouped rules.

    This function is the main entry point for rule loading:
    1. Reads the TSV file from the provided URL
    2. Converts mixed type columns to appropriate types
    3. Processes rule numbers for consistent grouping
    4. Validates rule numbers and collects messages
    5. Groups rules by rule number for execution

    Args:
        url: The URL to the TSV file containing rule definitions

    Returns:
        Tuple containing:
        - DataFrameGroupBy object with rules grouped by rule number (or None if error)
        - List of validation messages/warnings
    """
    try:
        # Read the TSV file
        # The TSV format is chosen for compatibility with Google Sheets
        # and other spreadsheet applications
        df = pd.read_csv(url, sep="\t")

        # Convert mixed type columns
        # This handles inconsistencies in spreadsheet data
        df = convert_mixed_columns(df)

        # Process rule numbers
        # This ensures all related conditions have the same rule number
        df = process_rule_numbers(df)

        # Get validation messages
        # These are warnings about potential issues with the rules
        messages = validate_rule_numbers(df)

        # Group by rule number
        # This creates a DataFrameGroupBy object that groups related conditions
        grouped_rules = df.groupby("Rule Number")

        return grouped_rules, messages

    except Exception as e:
        # Handle any errors in reading or processing the spreadsheet
        traceback.print_exc()
        return None, [f"Failed to read the TSV from the URL: {str(e)}:{e.with_traceback(None)}"]


def convert_mixed_columns(df: DataFrame) -> DataFrame:
    """Converts columns in a DataFrame to appropriate types based on their content.

    This handles common issues with spreadsheet data:
    1. Numeric columns that contain strings
    2. Mixed type columns
    3. Empty cells and NaN values

    The approach is to convert each column appropriately:
    - Numeric columns remain as numbers
    - Other columns are converted to strings, with empty strings for missing values

    Args:
        df: The DataFrame whose columns are to be converted

    Returns:
        DataFrame with columns converted to appropriate types
    """
    df = df.apply(
        lambda c: c
        if c.dropna().apply(lambda x: str(x).replace(".", "", 1).isdigit()).any()
        else c.map(lambda x: "" if pd.isna(x) else str(x))
    )

    return df
