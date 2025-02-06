import os

from dotenv import load_dotenv


def pytest_configure(config):
    load_dotenv(dotenv_path=".env")

    token_var = "SPECKLE_TOKEN"
    server_var = "SPECKLE_SERVER_URL"
    token = os.getenv(token_var)
    server = os.getenv(server_var)

    if not token:
        raise ValueError(f"Cannot run tests without a {token_var} environment variable")

    if not server:
        raise ValueError(
            f"Cannot run tests without a {server_var} environment variable"
        )

    # Set the token as an attribute on the config object
    config.SPECKLE_TOKEN = token
    config.SPECKLE_SERVER_URL = server
