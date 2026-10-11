#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"

color_info() { printf '\033[36m%s\033[0m\n' "$1"; }
color_ok() { printf '\033[32m%s\033[0m\n' "$1"; }

if [ ! -f "pyproject.toml" ]; then
    printf '\033[31m%s\033[0m\n' "Run this script from the repository root."
    exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
    color_info "Creating virtual environment in ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

color_info "Activating ${VENV_DIR}"
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

color_info "Upgrading pip"
python -m pip install --upgrade pip

color_info "Installing project with dev dependencies"
pip install -e ".[dev]"

if command -v pre-commit >/dev/null 2>&1; then
    color_info "Installing pre-commit hooks"
    pre-commit install
fi

color_ok "Development environment ready"
color_info "Activate with: source ${VENV_DIR}/bin/activate"