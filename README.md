# qc803_assignment

- [Overview](#overview)
- [Setup](#Setup)
    - [Installation](#installation)
- [Usage](#usage)
    - [Starting the Application](#starting-the-application)
- [Testing](#testing)
    - [Linting](#linting)
    - [Pytest](#pytest)

# Overview
GitHub repository for the QC803 final assignment for [[9,1,3]] Shor Code.

# Setup
## Installation
1. Clone the repository by running: git clone git@github.com:gegelendvay/qc803_assignment.git
2. Create a virtual environment in the project's root directory: pyhon3 -m venv .venv
3. Activate the virtual environment: . .venv/bin/activate

# Usage
## Starting the Application

> [!IMPORTANT]  
> Make sure to follow the [installation steps](#installation) before trying to start the application.

1. Activate the virtual environment: `. .venv/bin/activate`
2. Start the application by running: `python3 src/main.py`

# Testing
## Linting
To perform linting checks, run:
```bash
ruff check .
```

## Pytest
To run tests with `pytest` and generate a coverage report, run:
```bash
pytest -v --cov=. --cov-fail-under=85 --cov-report=term-missing:skip-covered --asyncio-mode=auto
```
