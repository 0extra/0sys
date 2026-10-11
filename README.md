# 0sys

A friendly server automation tool for beginner sysadmins.

## What is 0sys

0sys helps people who are just starting their journey as system
administrators. You do not need to know Ansible, Terraform, or any
other tool. You describe what you want in a simple configuration
file, and 0sys picks the right tool and does the work for you.

## Who is it for

- People who just learned `nano` and `cd`.
- People who want to set up their first VPS.
- People who are afraid to break something.
- People who want to understand what is happening.

## Features

- **Interactive wizard** — eight guided steps with plain-English hints
- **YAML configuration** — one file describes the whole server
- **Multiple backends** — Ansible, Shell, cloud-init for VPS providers
- **Deterministic planning** — see what will happen before it happens
- **Idempotent execution** — safe to run more than once
- **Plain-English explanations** — every step is explained
- **Built-in knowledge base** — ask what a term means right in the terminal
- **Audit log** — every action is recorded with secrets redacted
- **SQLite state** — inspect and roll back previous runs
- **SSH and local** — works on your machine or a remote server

## Installation

With pipx (recommended):

```bash
pipx install zerosys
```

From source:

```bash
git clone https://github.com/0extra/0sys.git
cd 0sys
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

With Docker:

```bash
docker build -f packaging/docker/Dockerfile -t 0sys .
docker run --rm -it 0sys --help
```

## Quick start

Create a configuration with the interactive wizard:

```bash
0sys init
```

Review the plan:

```bash
0sys plan 0sys.yaml
```

Explain what it will do in plain English:

```bash
0sys explain 0sys.yaml
```

Apply it:

```bash
0sys apply 0sys.yaml
```

Check the result without changing anything:

```bash
0sys check 0sys.yaml
```

## Commands

| Command | Purpose |
|---|---|
| `0sys init` | Create a starter config with the wizard |
| `0sys plan <config>` | Show the task graph without executing |
| `0sys apply <config>` | Apply the configuration |
| `0sys check <config>` | Dry-run: show what would change |
| `0sys explain <config>` | Explain each step in plain English |
| `0sys cloud-init <config>` | Generate cloud-init user-data for a VPS |
| `0sys rollback` | Inspect past runs and roll back |
| `0sys doctor` | Check the environment for missing pieces |
| `0sys examples` | Show example configurations |
| `0sys explain-term <term>` | Explain a technical term |
| `0sys tips <category>` | Show practical tips |

## Configuration example

```yaml
version: 1

server:
  hostname: web-01
  timezone: UTC

packages:
  install:
    - nginx
    - ufw
    - fail2ban

services:
  nginx:
    state: started
    enabled: true

users:
  - name: admin
    groups: [sudo]
    shell: /bin/bash
    sudo: true

firewall:
  default: deny
  allow: [22, 80, 443]
```

More examples in [examples/](examples/).

## How it works

1. 0sys reads your YAML configuration.
2. The validator checks it for common mistakes (firewall lockouts,
   conflicting packages, insecure users).
3. The planner builds a dependency graph of tasks.
4. For each task, 0sys picks the right backend: Ansible for system
   state, Shell for raw commands, cloud-init for VPS user-data.
5. The executor runs tasks level by level and shows you what happens.
6. Every action is recorded in the audit log and the state store.

## Backends

- **Ansible** — installs packages, manages services, users, files,
  and firewall rules. Requires `ansible-core` in `PATH`.
- **Shell** — runs raw shell commands on the target host.
- **cloud-init** — generates user-data for VPS providers. Offline
  backend; no execution on the target.

## Learn more

- [Getting started](docs/getting-started.md)
- [Concepts](docs/concepts.md)
- [Configuration reference](docs/config-reference.md)
- [Backends](docs/backends.md)
- [Wizard](docs/wizard.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).