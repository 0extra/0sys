# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Interactive wizard with eight guided steps and plain-English hints
- YAML configuration schema with strict validation
- Semantic validator with firewall, user, and package rules
- Task graph (DAG) with deterministic topological ordering
- Ansible backend with roles for server, packages, users, firewall, service, file
- Shell backend for raw commands
- Local and SSH connection layer with key permission checks
- SQLite state store with run and task history
- Audit log with JSONL output and secret redaction
- SSH key generation, fingerprinting, and permission hardening
- Knowledge base with glossary and tips, exposed via `0sys explain-term` and `0sys tips`
- Utility modules for filesystem, network, platform, shell, and text
- CLI commands: `init`, `plan`, `apply`, `check`, `rollback`, `doctor`, `examples`, `explain`, `explain-term`, `tips`
- GitHub Actions workflows for CI, lint, and release

### Fixed

- YAML output no longer includes empty sections
- Task order is now deterministic across runs
- SSH keypair generation handles overwrite flag correctly

## [0.1.0] - TBD

Initial public release.