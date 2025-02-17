import pandas as pd
from pandas import DataFrame


def read_rules_from_spreadsheet(url: str) -> DataFrame | None:
    """Reads a TSV file from a provided URL and returns a DataFrame.

    Args:
        url (str): The URL to the TSV file.

    Returns:
        DataFrame: Pandas DataFrame containing the TSV data.
    """
    try:
        # Since the output is a TSV, we use `pd.read_csv` with `sep='\t'` to specify tab-separated values.
        df = pd.read_csv(url, sep="\t")
        df = convert_mixed_columns(df)

        # Convert columns to appropriate types based on their content.
        return df

    except Exception as e:
        print(f"Failed to read the TSV from the URL: {e}")
        return None


def convert_mixed_columns(df):
    """Converts columns in a DataFrame to appropriate types based on their content.

    Args:
        df (DataFrame): The DataFrame whose columns are to be converted.

    Returns:
        DataFrame: The DataFrame with columns converted to appropriate types.
    """
    df = df.apply(lambda c: c.astype(object) if any(str(x).replace(".", "", 1).isdigit() for x in c) else c.astype(str))

    return df
