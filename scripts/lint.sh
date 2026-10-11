#!/usr/bin/env bash
set -euo pipefail

color_info() { printf '\033[36m%s\033[0m\n' "$1"; }
color_ok() { printf '\033[32m%s\033[0m\n' "$1"; }

if [ ! -d ".venv" ]; then
    printf '\033[31m%s\033[0m\n' "No .venv found. Run scripts/dev-setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

color_info "Running ruff check"
ruff check src tests

color_info "Running ruff format check"
ruff format src tests --check

color_info "Running mypy"
mypy src/zerosys

color_ok "All checks passed"