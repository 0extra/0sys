# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-18

Initial MVP release.

### Added
- Interactive wizard with eight guided steps
- YAML configuration schema with strict Pydantic validation
- Semantic validator that blocks SSH lockouts (FW001, FW005)
- Task graph (DAG) with deterministic topological ordering
- Ansible backend with roles for server, packages, users, firewall, service, file, and 0TPE
- Shell backend for raw commands
- Local and SSH connection layer with key permission checks
- SQLite state store with run and task history
- Audit log with JSONL output and secret redaction
- Knowledge base with glossary and tips (`0sys explain-term`, `0sys tips`)
- Utility modules for filesystem, network, platform, shell, and text
- CLI commands: `init`, `plan`, `apply`, `check`, `rollback`, `doctor`, `examples`, `explain`, `explain-term`, `tips`, `cloud-init`, `terraform`, `nixos`, `0tpe`
- Integration tests using testcontainers for apply, idempotency, and rollback
- GitHub Actions workflows for CI, lint, and release

### Changed
- Rollback is safe by default (only reverts tasks that changed the system).
- Removing users and packages during rollback requires `--aggressive`.
- Run state is saved task by task, allowing rollback of interrupted runs.
- Secrets are redacted before being written to the SQLite database.
- Database file is created with mode 0600.
- Ansible host keys are pinned in a persistent `known_hosts` file.
- The `0tpe` role defaults to version 0.1.8 and generates random tokens.

### Fixed
- YAML output no longer includes empty sections.
- Task order is deterministic across runs.
- SSH keypair generation handles overwrite flag correctly.
- Package, group, shell, and SNI inputs are validated against shell injection.