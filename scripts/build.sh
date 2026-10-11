#!/usr/bin/env bash
set -euo pipefail

DIST_DIR="dist"

color_info() { printf '\033[36m%s\033[0m\n' "$1"; }
color_ok() { printf '\033[32m%s\033[0m\n' "$1"; }

if [ ! -d ".venv" ]; then
    printf '\033[31m%s\033[0m\n' "No .venv found. Run scripts/dev-setup.sh first."
    exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

color_info "Cleaning previous builds"
rm -rf "${DIST_DIR}" build ./*.egg-info

color_info "Installing build tools"
pip install --quiet --upgrade build

color_info "Building wheel and sdist"
python -m build

color_ok "Build artifacts:"
ls -lh "${DIST_DIR}"