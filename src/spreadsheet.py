import pandas as pd


def read_rules_from_spreadsheet(url):
    """Reads a TSV file from a provided URL and returns a DataFrame.

    Args:
        url (str): The URL to the TSV file.

    Returns:
        DataFrame: Pandas DataFrame containing the TSV data.
    """
    try:
        # Since the output is a TSV, we use `pd.read_csv` with `sep='\t'` to specify tab-separated values.
        return pd.read_csv(url, sep="\t")
    except Exception as e:
        print(f"Failed to read the TSV from the URL: {e}")
        return None
