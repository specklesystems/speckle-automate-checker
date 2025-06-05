#!/bin/sh

# Store the current Python environment
CURRENT_ENV=$(pip freeze)

# Remove dev dependencies
pip uninstall -y pytest pytest-cov isort flake8 ruff

# Generate production requirements
pip freeze > requirements.txt

# Reinstall dev dependencies
pip install pytest pytest-cov isort flake8 ruff

# Generate dev requirements
pip freeze > requirements-dev.txt

# Restore the original environment
pip uninstall -y pytest pytest-cov isort flake8 ruff
echo "$CURRENT_ENV" | pip install -r /dev/stdin

echo "Requirements files have been updated successfully!" 