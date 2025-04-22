# Developing Enhanced Crawler

This document provides guidance for developers working on the Enhanced Crawler project.

## Development Environment Setup

This project uses Poetry for dependency management.

1.  **Install Poetry:** If you don't have Poetry installed, follow the official installation guide: [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation)
2.  **Install Dependencies:** Navigate to the project's root directory in your terminal and run:
    ```bash
    poetry install --no-root
    ```
    This will install all project dependencies.
3.  **Activate the Virtual Environment:** Poetry creates a virtual environment for the project. You can activate it using:
    ```bash
    poetry shell
    ```
    Alternatively, Poetry can automatically use the virtual environment when running commands with `poetry run`.

## Running Tests

Unit tests are configured using pytest and can be run via the Makefile.

To run all unit tests, use the following command in the project's root directory:

```bash
make test
```

## Linting and Formatting

This project uses Ruff for linting and formatting. The linting and formatting checks are integrated into the Makefile.

To run the linter and formatter with autocorrection, use:

```bash
make lint
```

This command will run both `make autocorrect` (which applies automatic fixes) and `make format` (which formats the code).

You can also run the full check (linting and testing) using:

```bash
make check