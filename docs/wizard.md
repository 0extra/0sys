# Wizard

The interactive wizard builds a configuration file by asking questions.
It is designed for people who have never configured a server before.

## Starting the wizard

```bash
0sys init
```

You can specify the output path:

```bash
0sys init -o my-server.yaml
```

## Steps

### 1. Welcome

A short introduction. Nothing to answer.

### 2. Server identity

- **Hostname** — what the server calls itself. Suggested value is your
  current computer's hostname. Change it if you plan to use a different
  name in DNS.
- **Timezone** — used in logs and scheduled tasks. `UTC` is safe
  everywhere. Change only if you have a reason.
- **Locale** — language and character set. `en_US.UTF-8` is the safest
  default.

### 3. Preset

Choose a starting point:

- **Minimal** — just secure a fresh server. Installs ufw and fail2ban.
  Opens only SSH.
- **Web server** — adds nginx and opens ports 80 and 443.
- **Docker host** — adds Docker and docker-compose. Opens only SSH.
- **Custom** — you pick each piece in later steps.

You can override any of these in the remaining steps.

### 4. SSH hardening

- **Create an admin user** — recommended. This is a personal account
  with sudo access, so you do not need to log in as root.
- **Username** — anything you like. `admin` or `deploy` are common.
- **SSH key** — path to your public key. If you leave it empty, login
  will use a password. Not recommended on a public server.
- **Disable password login** — only offered if a key was provided.
  Strongly recommended once your key works.

### 5. Firewall and protection

- **Close all ports by default** — recommended. Only ports you list
  are reachable from the internet.
- **Ports to open** — SSH (22), HTTP (80), HTTPS (443), and database
  ports. You can pick multiple.
- **Install fail2ban** — watches logs and blocks IPs that keep trying
  to log in. Recommended on every public server.

### 6. Services

- **nginx** — web server. Choose if you plan to host a website.
- **Docker** — container runtime. Choose if you plan to run containers.

### 7. Extra packages

Anything else you want installed. Comma-separated list. For example:
`vim, tmux, htop, git`.

### 8. Review

A summary table of every choice. Answer `yes` to write the file, `no`
to cancel without writing anything.

## After the wizard

The wizard writes a YAML file. It does not touch the server.

Next steps:

```bash
0sys plan 0sys.yaml
0sys explain 0sys.yaml
0sys apply 0sys.yaml
```

## Non-interactive use

If you do not want the wizard, use a preset:

```bash
0sys init --preset web --hostname web-01 -o prod.yaml
```

Available presets: `minimal`, `web`, `docker`.