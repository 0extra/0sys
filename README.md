# 0sys

**Friendly server automation for people who are just getting started, but don't want to hit a ceiling.**

Write one YAML file. 0sys validates it, plans the work, picks the right tool
(Ansible, cloud-init, Terraform, NixOS), and explains every step in plain
English.

## What 0sys is

0sys is a **planner, validator, and teacher** for server automation. It sits
on top of tools like Ansible and Terraform so you do not have to learn them
first.

You describe what you want:

```yaml
version: 1
server:
  hostname: web-01
packages:
  install: [nginx, ufw, fail2ban]
firewall:
  default: deny
  allow: [22, 80, 443]
```

Run three commands:

```bash
0sys plan 0sys.yaml    # see what will happen
0sys explain 0sys.yaml # read why, in plain English
0sys apply 0sys.yaml   # do it
```

That's it. No playbooks, no `.tf` files, no Jinja templates.

## What 0sys is not

0sys is **not a replacement for Ansible or Terraform**. It is a layer in
front of them. See [docs/positioning.md](docs/positioning.md) for details.

- **Ansible** is a backend. 0sys generates playbooks and calls
  `ansible-runner` under the hood.
- **Terraform** is a backend. 0sys generates `.tf` files for you to run.
- **cloud-init** is a backend. 0sys generates `user-data` for VPS providers.
- **NixOS** is a backend. 0sys generates `configuration.nix`.
- **Shell** is a backend. Used only for raw commands.

0sys decides which backend fits each task based on the kind of work.

## Who 0sys is for

- **Beginners** who just learned `nano` and `cd` and want a real server.
- **Intermediate users** who know some Linux but find Ansible verbose.
- **Advanced users** who want a quick scaffolder for Terraform, cloud-init,
  or NixOS without typing boilerplate.

## Feature status

Honest view of what is done and what is not.

| Feature | Status | Notes |
|---|---|---|
| YAML config + schema | **stable** | Pydantic v2, strict validation |
| Config validator | **stable** | Catches firewall lockouts, package conflicts, unsafe users |
| Task planner (DAG) | **stable** | Deterministic order, cycle detection |
| Shell backend | **stable** | Raw commands, no idempotency |
| Ansible backend | **stable** | 9 roles included |
| Audit log + state store | **stable** | SQLite + JSONL, secrets redacted |
| CLI commands | **stable** | 12 commands |
| Wizard (8 steps) | **beta** | Interactive, works, limited automated tests |
| Knowledge base | **beta** | 12 terms, 7 tip categories |
| Rollback | **beta** | Only for files, users, services, packages |
| cloud-init backend | **beta** | Hetzner, DigitalOcean, generic |
| Terraform backend | **beta** | Hetzner, DigitalOcean |
| NixOS backend | **beta** | Common services only |
| 0TPE proxy backend | **beta** | Docker-based deploy |
| Remote apply over SSH | **beta** | Works, tested manually |
| Integration tests | **planned** | testcontainers, not yet added |
| Plugin architecture | **planned** | For third-party backends |

## Installation

Requires Python 3.11 or newer.

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

For the Ansible backend, install Ansible separately:

```bash
# Debian / Ubuntu
sudo apt install ansible

# Fedora / RHEL
sudo dnf install ansible

# Arch
sudo pacman -S ansible

# macOS
brew install ansible
```

## Quick start

Create a configuration with the interactive wizard:

```bash
0sys init
```

Review it, read the explanation, then apply:

```bash
0sys plan 0sys.yaml
0sys explain 0sys.yaml
0sys apply 0sys.yaml --host 192.0.2.10 --user admin --ssh-key ~/.ssh/id_ed25519
```

Check the result without changing anything:

```bash
0sys check 0sys.yaml
```

## Commands

| Command | Purpose |
|---|---|
| `0sys init` | Create a starter config (interactive wizard) |
| `0sys plan <config>` | Show the task graph without executing |
| `0sys apply <config>` | Apply the configuration |
| `0sys check <config>` | Dry-run: show what would change |
| `0sys explain <config>` | Explain each step in plain English |
| `0sys rollback [run_id]` | Inspect past runs, roll back safe operations |
| `0sys doctor` | Check environment for missing pieces |
| `0sys examples` | Show example configurations |
| `0sys explain-term <term>` | Explain a technical term |
| `0sys tips <category>` | Show practical tips |
| `0sys cloud-init <config>` | Generate user-data for a VPS provider |
| `0sys terraform <config>` | Generate Terraform HCL |
| `0sys nixos <config>` | Generate NixOS configuration.nix |
| `0sys 0tpe <subcommand>` | Manage the 0TPE proxy server |

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
    ssh_key: "ssh-ed25519 AAAA..."

firewall:
  default: deny
  allow: [22, 80, 443]
```

More in [examples/](examples/).

## Backends

0sys does not do the work itself. It picks one of five backends for each task.

- **Ansible** — packages, services, users, firewall, files, 0TPE proxy.
  Requires `ansible-core`. Talks over SSH.
- **Shell** — raw commands on the target. Not idempotent.
- **cloud-init** — generates user-data for VPS providers. Offline.
- **Terraform** — generates HCL for infrastructure. Offline.
- **NixOS** — generates `configuration.nix`. Offline.

See [docs/backends.md](docs/backends.md) for details and examples.

## How it works

1. 0sys reads your YAML configuration.
2. The validator checks for common mistakes and refuses to plan if any
   are critical (firewall lockouts, `sudo` with disabled shell, etc.).
3. The planner builds a task graph with deterministic order.
4. For each task, 0sys picks a backend based on the task kind.
5. The executor runs tasks level by level, showing progress and
   explanations.
6. Every action is recorded in SQLite state and a redacted audit log.
7. `0sys rollback` can undo reversible tasks from a previous run.

## Learning resources

- [Getting started](docs/getting-started.md) — install and run your first config
- [Positioning](docs/positioning.md) — how 0sys differs from Ansible, Terraform, cloud-init
- [Concepts](docs/concepts.md) — how 0sys thinks about servers
- [Configuration reference](docs/config-reference.md) — every field explained
- [Backends](docs/backends.md) — how 0sys talks to servers
- [Wizard](docs/wizard.md) — guided setup for beginners
- [FAQ](docs/faq.md) — common questions
- [Troubleshooting](docs/troubleshooting.md) — what to do when things break

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).