# Backends

A backend is what actually does the work on the target. 0sys picks a
backend automatically based on the task, but you can override with
`--backend <name>` on `plan`, `apply`, and `check`.

## Ansible

The default backend for system state.

**Handles:** `server`, `packages.install`, `packages.remove`,
`services`, `users`, `firewall`, `files`.

**Requires:** `ansible-core` installed and `ansible-playbook` in `PATH`.

**How it works:** 0sys generates a playbook in a temporary directory and
runs it with `ansible-runner`. The target is reached over SSH.

**Install Ansible:**

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

**Roles included:**

- `base` — hostname, timezone, locale
- `packages` — install and update cache
- `users` — user, sudo, authorized key
- `firewall` — ufw on Debian, firewalld on Red Hat
- `service` — generic service with config file
- `file` — copy with permissions
- `nginx`, `docker`, `fail2ban`, `ssh-hardening` — ready-made roles

## Shell

Raw commands on the target.

**Handles:** `commands`.

**How it works:** for local targets, runs the command directly. For
remote targets, runs it over SSH.

**Requires:** `ssh` in `PATH` for remote targets.

Use this backend sparingly. Shell commands are not idempotent.

## cloud-init

Generates `user-data` files for VPS providers.

**Handles:** nothing. It is an offline backend.

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

- Hetzner Cloud
- DigitalOcean
- Vultr
- Linode
- AWS EC2
- Google Cloud
- Oracle Cloud

## Choosing a backend

You rarely need to. The resolver picks based on task kind. Override
only when you have a reason:

```bash
0sys plan 0sys.yaml --backend shell
```

All tasks will try to run via Shell. This is useful for debugging but
unusual in practice.