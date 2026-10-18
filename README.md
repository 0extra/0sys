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
0sys plan 0sys.yaml
0sys explain 0sys.yaml
0sys apply 0sys.yaml
```

That's it. No playbooks, no `.tf` files, no Jinja templates.

## What 0sys is not

0sys is **not a replacement for Ansible or Terraform**. It is a layer in
front of them.

- **Ansible** is a backend. 0sys generates playbooks and calls `ansible-runner`.
- **Terraform** is a backend. 0sys generates `.tf` files.
- **cloud-init** is a backend. 0sys generates `user-data` for VPS providers.
- **NixOS** is a backend. 0sys generates `configuration.nix`.
- **Shell** is a backend. Used only for raw commands.

## Who 0sys is for

- **Beginners** who just learned `nano` and `cd` and want a real server.
- **Intermediate users** who know some Linux but find Ansible verbose.
- **Advanced users** who want a quick scaffolder for Terraform or NixOS.

## Feature status

This is an early release (v0.1.0). The core logic is stable, but
integrations and interactive tools are still in beta.

| Feature | Status | Notes |
|---|---|---|
| Config validator | **stable** | Blocks SSH lockouts (FW001, FW005), package conflicts, unsafe users |
| Task planner (DAG) | **stable** | Deterministic order, cycle detection |
| Shell backend | **stable** | Raw commands, no idempotency |
| Ansible backend | **stable** | Tested on Ubuntu: base, packages, service, users, firewall |
| Audit log + state store | **stable** | SQLite + JSONL, secrets redacted, DB mode 0600 |
| CLI commands | **stable** | 14 commands, proper flat routing |
| Knowledge base | **stable** | 12 terms, 7 tip categories |
| Wizard (8 steps) | **beta** | Interactive, works, has mock tests but needs real-user feedback |
| Rollback | **beta** | Tested on users and files; packages need `--aggressive` |
| cloud-init backend | **beta** | Generates valid YAML, untested on live VPS providers |
| Terraform backend | **beta** | Generates valid HCL, untested on live cloud APIs |
| NixOS backend | **beta** | Generates valid config, untested on a real NixOS install |
| 0TPE proxy backend | **beta** | Docker-based deploy, requires live testing |
| Integration tests | **stable** | testcontainers, cover apply, idempotency, rollback |

## Known limitations

- `server.ssh_port` is used only by the validator; 0sys does not change the port sshd listens on.
- The firewall role opens TCP ports only and never closes ports removed from the config.
- `apply` runs one Ansible invocation per task, so large configs are slow.
- The 0TPE role fetches a git tag; set `proxy.commit_sha` to pin an exact revision.

## Installation

Requires Python 3.11 or newer.

```bash
pipx install zerosys
```

Or from source:

```bash
git clone https://github.com/0extra/0sys.git
cd 0sys
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick start

```bash
0sys init
0sys plan 0sys.yaml
0sys apply 0sys.yaml --host 192.0.2.10 --user admin --ssh-key ~/.ssh/id_ed25519
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

## License

Apache License 2.0. See [LICENSE](LICENSE).