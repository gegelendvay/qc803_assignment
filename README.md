# qc803_assignment

- [Overview](#overview)
- [Setup](#Setup)
    - [Installation](#installation)
- [Usage](#usage)
    - [Starting the Application](#starting-the-application)
    - [Experiment Outcomes](#experiment-outcomes)
- [Testing](#testing)
    - [Linting](#linting)
    - [Pytest](#pytest)

# Overview
GitHub repository for the QC803 final assignment for [[9,1,3]] Shor Code.

# Setup
## Installation
1. Clone the repository by running: git clone `git@github.com:gegelendvay/qc803_assignment.git`
2. Create a virtual environment in the project's root directory: `pyhon3 -m venv .venv`
3. Activate the virtual environment: `. .venv/bin/activate`
4. Install the required dependencies using either of the following commands: `python3 -m pip install .` or `pip install -r requirements.txt`

# Usage
## Starting the Application

> [!IMPORTANT]  
> Make sure to follow the [installation steps](#installation) before trying to start the application.

1. Activate the virtual environment: `. .venv/bin/activate`
2. Start the application by running: `python3 src/main.py`

Optionally, command line arguments can be added to the above command:

|      Argument     |             Description            | Type | Default |
|:-----------------:|:----------------------------------:|:----:|:-------:|
| --num-simulations | Number of simulations to run       |  int |       1 |
| --arbitrary-error | Arbitrary error type               |  str |       - |
|   --qubit-error   | Index of a qubit to apply error on |  int |       - |
|   --input-state   | Initial logical state              |  int |       - |
|   --draw-circuit  | Save circuit diagrams              | bool |   False |

## Experiment Outcomes
The outcome of the experiments can be found in the following file: `results_histogram.png`.

When using the `--draw-circuit` command line argument, a diagram of the circuit will be saved to `circuit_{s}.png` file, where `s` is the index of the simulation.

When executing the `plot_comparison.py` file, results will be saved to `shor_syndrome_comparison.png`.

# Testing
## Linting
To perform linting checks, run:
```bash
ruff check .
```

## Pytest
To run tests with `pytest` and generate a coverage report, run:
```bash
pytest -v --cov=. --cov-fail-under=85 --cov-report=term-missing:skip-covered
```
