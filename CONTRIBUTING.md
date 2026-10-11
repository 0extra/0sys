# Contributing to 0sys (pls)

Thanks for considering a contribution. This document explains how to set up
the project, run the tests, and submit changes.

## Requirements

- Python 3.11 or newer
- Git
- Ansible (only needed for full integration tests)

## Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/0extra/0sys.git
cd 0sys
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Running tests

```bash
pytest
```

To run only unit tests:

```bash
pytest tests/unit
```

To run a single test file:

```bash
pytest tests/unit/test_config_parser.py
```

## Linting and type checking

```bash
ruff check src tests
ruff format src tests --check
mypy src/zerosys
```

Fix formatting automatically:

```bash
ruff check src tests --fix
ruff format src tests
```

## Style guide

- Python 3.11 features are allowed (`StrEnum`, `X | Y` unions).
- No comments in code unless absolutely necessary.
- All text, code, and docstrings in English.
- Type annotations required on all public functions.
- Tests follow the Arrange-Act-Assert pattern.
- Prefer small, focused modules over large ones.

## Commit messages

Use the following prefixes:

- `feat:` new feature
- `fix:` bug fix
- `refactor:` code change that does not add a feature or fix a bug
- `test:` adding or changing tests
- `docs:` documentation only
- `chore:` build, dependencies, tooling

Example:

```
feat: add docker backend for container workloads
```

## Pull request process

1. Fork the repository and create a branch.
2. Make your changes.
3. Ensure all checks pass locally: `ruff`, `mypy`, `pytest`.
4. Update `CHANGELOG.md` under `[Unreleased]` if the change is user-facing.
5. Open a pull request against `main`.
6. Wait for CI to pass and address review feedback.

## Reporting issues

Use the issue templates in `.github/ISSUE_TEMPLATE/`. Include:

- 0sys version (`0sys --version`)
- Python version
- Operating system
- The config file or command that triggered the problem

## License

By contributing, you agree that your contributions are licensed under the
Apache License 2.0. See [LICENSE](LICENSE).