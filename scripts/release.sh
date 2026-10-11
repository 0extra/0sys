#!/usr/bin/env bash
set -euo pipefail

color_info() { printf '\033[36m%s\033[0m\n' "$1"; }
color_ok() { printf '\033[32m%s\033[0m\n' "$1"; }
color_err() { printf '\033[31m%s\033[0m\n' "$1"; }

if [ $# -ne 1 ]; then
    color_err "Usage: $0 <version>"
    color_err "Example: $0 0.2.0"
    exit 1
fi

VERSION="$1"

if ! echo "${VERSION}" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    color_err "Version must be semver: MAJOR.MINOR.PATCH"
    exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
    color_err "Working directory is not clean. Commit or stash your changes first."
    exit 1
fi

color_info "Bumping version to ${VERSION}"
sed -i.bak "s/^__version__ = .*/__version__ = \"${VERSION}\"/" src/zerosys/version.py
sed -i.bak "s/^__version_info__ = .*/__version_info__ = ($(echo "${VERSION}" | sed 's/\./, /g'))/" src/zerosys/version.py
sed -i.bak "s/^version = .*/version = \"${VERSION}\"/" pyproject.toml
rm -f src/zerosys/version.py.bak pyproject.toml.bak

color_info "Committing version bump"
git add src/zerosys/version.py pyproject.toml
git commit -m "chore: release v${VERSION}"

color_info "Tagging v${VERSION}"
git tag -a "v${VERSION}" -m "Release v${VERSION}"

color_ok "Release v${VERSION} prepared"
color_info "Push with: git push && git push --tags"