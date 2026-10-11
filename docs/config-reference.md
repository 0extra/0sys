# Configuration reference

The 0sys configuration is a single YAML file. Every section is optional.
If a section is missing, 0sys does nothing in that area.

## Top-level fields

| Field | Type | Description |
|---|---|---|
| `version` | int | Config schema version. Currently `1`. |
| `server` | mapping | Base server settings |
| `packages` | mapping | Packages to install or remove |
| `services` | mapping | Services to manage |
| `users` | list | Users to create |
| `firewall` | mapping | Firewall rules |
| `files` | list | Files to upload |
| `commands` | list | Raw shell commands |

## `server`

| Field | Type | Description |
|---|---|---|
| `hostname` | string | The server's name |
| `timezone` | string | e.g. `UTC`, `Europe/Moscow` |
| `locale` | string | e.g. `en_US.UTF-8` |

## `packages`

| Field | Type | Description |
|---|---|---|
| `install` | list of strings | Packages to install |
| `remove` | list of strings | Packages to remove |

You cannot list the same package in both `install` and `remove`.

## `services`

A mapping from service name to service settings.

| Field | Type | Default | Description |
|---|---|---|---|
| `state` | string | `started` | `started`, `stopped`, `restarted`, `reloaded` |
| `enabled` | bool | `true` | Start on boot |
| `config_file` | string | none | Local file to upload before restarting |

## `users`

A list of users to create.

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | required | Username |
| `groups` | list of strings | `[]` | Additional groups |
| `ssh_key` | string | none | Public key to authorize |
| `shell` | string | `/bin/bash` | Login shell |
| `sudo` | bool | `false` | Grant passwordless sudo |

Names must be unique. Names must start with a letter and may contain
letters, digits, dashes, and underscores.

## `firewall`

| Field | Type | Default | Description |
|---|---|---|---|
| `default` | string | `deny` | `deny` or `allow` |
| `allow` | list of ints | `[]` | TCP ports to open |

If `default` is `deny` and port 22 is not listed, the validator raises
an error. This prevents locking yourself out.

## `files`

A list of files to upload.

| Field | Type | Default | Description |
|---|---|---|---|
| `src` | string | required | Local path |
| `dest` | string | required | Absolute path on target |
| `owner` | string | `root` | File owner |
| `group` | string | `root` | File group |
| `mode` | string | `0644` | Octal file mode |

## `commands`

A list of raw shell commands.

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | required | Human-readable label |
| `run` | string | required | Shell command to execute |
| `when` | string | `once` | `once`, `always`, `changed` |

Commands are not idempotent. They run every time unless `when: once`
and 0sys can tell from state that they already ran. In practice, use
commands only when no other task type fits.

## Example

```yaml
version: 1

server:
  hostname: web-01
  timezone: UTC
  locale: en_US.UTF-8

packages:
  install: [nginx, ufw, fail2ban]
  remove: [apache2]

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

files:
  - src: ./files/nginx.conf
    dest: /etc/nginx/nginx.conf
    mode: "0644"

commands:
  - name: reload-nginx
    run: systemctl reload nginx
    when: once
```