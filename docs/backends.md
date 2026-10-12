# Backends

0sys does not do the work itself. It picks a backend for each task
based on the task kind. Five backends are supported.

You can override the choice with `--backend <name>` on `plan`, `apply`,
and `check`.

## Ansible

The default backend for anything that configures an existing server.

**Handles:** `server`, `packages.install`, `packages.remove`,
`services`, `users`, `firewall`, `files`, `proxy`.

**Requires:**

- `ansible-core` installed and `ansible-playbook` in `PATH`
- `community.docker` collection if you use the `proxy` section
  (`ansible-galaxy collection install community.docker`)

**How it works:** 0sys generates a playbook in a temporary directory and
runs it with `ansible-runner`. The target is reached over SSH.

**Roles included:**

- `base` — hostname, timezone, locale
- `packages` — install and update cache
- `users` — user, sudo, authorized key
- `firewall` — ufw on Debian, firewalld on Red Hat
- `service` — generic service with optional config file
- `file` — copy with permissions
- `nginx` — install and enable nginx
- `docker` — install docker and docker-compose
- `fail2ban` — install and enable fail2ban
- `ssh-hardening` — disable password login and root login
- `0tpe` — build and run the 0TPE proxy in Docker

## Shell

Raw commands on the target. Use sparingly.

**Handles:** `commands`.

**How it works:** for local targets, runs the command directly. For
remote targets, runs it over SSH.

**Requires:** `ssh` in `PATH` for remote targets.

Shell commands are **not idempotent**. Use them only when no other task
type fits.

## cloud-init

Generates `user-data` files for VPS providers.

**Handles:** nothing. Offline backend; does not execute anything.

**How it works:** you run `0sys cloud-init <config>` and get a YAML
file. Paste it into your provider's user-data field when creating a
server. cloud-init runs the file on first boot.

**Supported features:**

- Hostname, timezone, locale
- Package installation
- User creation with SSH keys and sudo
- Firewall rules (ufw)
- Service start and enable
- File writes
- Raw commands

**Providers that support user-data:**

Hetzner Cloud, DigitalOcean, Vultr, Linode, AWS EC2, Google Cloud,
Oracle Cloud, and most others.

## Terraform

Generates `.tf` files for creating infrastructure.

**Handles:** nothing. Offline backend.

**How it works:** you run `0sys terraform <config>` and get a directory
with `main.tf`, `variables.tf`, `outputs.tf`. Run `terraform init`,
`terraform plan`, `terraform apply` yourself.

**Supported providers:**

- Hetzner Cloud (`hcloud_server`)
- DigitalOcean (`digitalocean_droplet`)

**Requires:** `terraform` CLI, provider API token.

## NixOS

Generates a `configuration.nix` file.

**Handles:** nothing. Offline backend.

**How it works:** you run `0sys nixos <config>` and get
`configuration.nix`. Place it next to `hardware-configuration.nix` and
run `nixos-rebuild switch`.

**Supported sections:**

- Hostname, timezone, locale
- Packages (`environment.systemPackages`)
- Services (nginx, openssh, fail2ban, docker, postgresql, mysql, redis)
- Users with SSH keys and wheel group
- Firewall (allowedTCPPorts)
- Files under `/etc`

## Choosing a backend

You rarely need to. The resolver picks automatically:

- Anything that changes server state → Ansible
- `commands` → Shell
- Offline generators (cloud-init, Terraform, NixOS) → invoked via their
  own CLI commands, not via `apply`

Override only when debugging:

```bash
0sys plan 0sys.yaml --backend shell
```

This forces every task through Shell. Useful to see the raw commands
Ansible would run, but not recommended in practice.