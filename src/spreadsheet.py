"""Module for reading and processing rules from a cloud hosted TSV file."""

import pandas as pd
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy


def process_rule_numbers(df: DataFrame) -> DataFrame:
    """Process rule numbers in a DataFrame while preserving original rule identifiers.

    Makes no assumptions about rule number format - preserves them exactly as provided.
    Only generates new numbers (as integers) when no rule number exists.

    Args:
        df: DataFrame with columns including 'Rule Number' and 'Logic'

    Returns:
        DataFrame with processed rule numbers
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
    """Validate rule numbers and return any warnings or errors.

    Args:
        df: DataFrame with processed rule numbers

    Returns:
        List of warning/error messages
    """
    messages = []

    # Check for missing rule numbers
    if df["Rule Number"].isna().any():
        messages.append("Warning: Some rules are missing rule numbers")

    # Check for non-integer rule numbers
    non_int_mask = df["Rule Number"].apply(lambda x: not pd.isna(x) and not float(x).is_integer())
    if non_int_mask.any():
        messages.append("Warning: Some rule numbers are not integers")

    # Check for duplicate rule numbers in WHERE rows
    where_rules = df[df["Logic"].str.upper() == "WHERE"]["Rule Number"]
    duplicates = where_rules[where_rules.duplicated()]
    if not duplicates.empty:
        messages.append(f"Warning: Duplicate rule numbers found: {list(duplicates)}")

    return messages


def read_rules_from_spreadsheet(url: str) -> tuple[DataFrameGroupBy, list[str]] | tuple[None, list[str]]:
    """Reads a TSV file from a provided URL, processes rule numbers, and returns grouped rules.

    Args:
        url (str): The URL to the TSV file

    Returns:
        Tuple containing:
        - DataFrameGroupBy object with rules grouped by rule number (or None if error)
        - List of validation messages/warnings
    """
    try:
        # Read the TSV file
        df = pd.read_csv(url, sep="\t")

        # Convert mixed type columns
        df = convert_mixed_columns(df)

        # Process rule numbers
        df = process_rule_numbers(df)

        # Get validation messages
        messages = validate_rule_numbers(df)

        # Group by rule number
        grouped_rules = df.groupby("Rule Number")

        return grouped_rules, messages

    except Exception as e:
        return None, [f"Failed to read the TSV from the URL: {str(e)}"]


def convert_mixed_columns(df: DataFrame) -> DataFrame:
    """Converts columns in a DataFrame to appropriate types based on their content.

    null or empty strings are converted to empty strings instead of NaN.

    Args:
        df (DataFrame): The DataFrame whose columns are to be converted

    Returns:
        DataFrame with columns converted to appropriate types
    """
    df = df.apply(
        lambda c: c
        if c.dropna().apply(lambda x: str(x).replace(".", "", 1).isdigit()).any()
        else c.map(lambda x: "" if pd.isna(x) else str(x))
    )

    return df
