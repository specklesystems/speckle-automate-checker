# Checker Function Development Guide

## Setup

1. Install dependencies:

```bash
poetry shell && poetry install
```

2. Configure `.env`:

```
SPECKLE_TOKEN=your_speckle_token
SPECKLE_SERVER_URL=app.speckle.systems
```

Get test automation details from app.speckle.systems

## Project Structure

- `function.py`: Main business logic
- `rules.py`: Rule definitions and processing
- `inputs.py`: Function input schema
- `helpers.py`: Utility functions
- `spreadsheet.py`: TSV handling

## Testing

```bash
poetry run pytest
```

## Extending Rules

1. Add new predicate to `input_predicate_mapping` in `rules.py`
2. Create corresponding method in `PropertyRules` class
3. Update tests

## Building

The function is packaged as a Docker container:

```bash
docker build -f ./Dockerfile -t checker .
```

## Local Testing

```bash
docker run --rm checker python -u main.py run [automation_data] [parameters] [token]
```

## Deployment

Create a GitHub release to trigger deployment to Speckle Automate.