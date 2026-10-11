#!/usr/bin/env bash
set -euo pipefail

REPO="0extra/0sys"
BRANCH="main"
INSTALL_DIR="${HOME}/.local/share/0sys"
BIN_DIR="${HOME}/.local/bin"
PIPX_HOME="${HOME}/.local/pipx"

color_ok() { printf '\033[32m%s\033[0m\n' "$1"; }
color_err() { printf '\033[31m%s\033[0m\n' "$1"; }
color_info() { printf '\033[36m%s\033[0m\n' "$1"; }

detect_os() {
    case "$(uname -s)" in
        Linux*) echo "linux" ;;
        Darwin*) echo "macos" ;;
        *) echo "unknown" ;;
    esac
}

check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        color_err "python3 not found. Install Python 3.11 or newer."
        exit 1
    fi
    version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    major="${version%.*}"
    minor="${version#*.}"
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
        color_err "Python 3.11+ required, found ${version}."
        exit 1
    fi
    color_ok "Python ${version} detected"
}

ensure_pipx() {
    if command -v pipx >/dev/null 2>&1; then
        color_ok "pipx already installed"
        return
    fi
    color_info "Installing pipx"
    python3 -m pip install --user --upgrade pipx
    python3 -m pipx ensurepath
}

install_from_git() {
    color_info "Installing 0sys from git"
    pipx install "git+https://github.com/${REPO}.git@${BRANCH}"
}

install_from_source() {
    color_info "Installing 0sys from current directory"
    pipx install .
}

install_from_pypi() {
    color_info "Installing 0sys from PyPI"
    pipx install zerosys
}

main() {
    os=$(detect_os)
    if [ "$os" = "unknown" ]; then
        color_err "Unsupported operating system."
        exit 1
    fi

    check_python
    ensure_pipx

    if [ -f "pyproject.toml" ] && grep -q 'name = "zerosys"' pyproject.toml 2>/dev/null; then
        install_from_source
    else
        install_from_git
    fi

    mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"

    if ! echo "${PATH}" | grep -q "${BIN_DIR}"; then
        color_info "Add ${BIN_DIR} to PATH if not already present:"
        color_info "  export PATH=\"${BIN_DIR}:\$PATH\""
    fi

    if command -v 0sys >/dev/null 2>&1; then
        color_ok "0sys installed successfully"
        color_info "Run: 0sys doctor"
    else
        color_err "Installation finished but 0sys not found on PATH."
        exit 1
    fi
}

main "$@"