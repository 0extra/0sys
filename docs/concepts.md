# Concepts

0sys is built on a few simple ideas. Understanding them makes the tool
easier to use.

## Configuration as intent

You describe the state you want, not the commands to run. Instead of
"install nginx and start it", you write:

```yaml
packages:
  install: [nginx]
services:
  nginx:
    state: started
    enabled: true
```

0sys figures out what to do. If nginx is already installed and running,
nothing happens. If it is missing, 0sys installs it. If it is stopped,
0sys starts it.

## Idempotency

An operation is idempotent when running it twice has the same effect as
running it once. 0sys aims for every task to be idempotent. This means
you can safely apply the same config again and again.

Raw shell commands are the exception. If you write a command that is not
idempotent, 0sys will run it every time. Use commands sparingly.

## The task graph

When you run `0sys plan`, the output is a tree, not a list. This tree is
called a task graph.

Tasks at the same level have no dependencies on each other. Tasks at a
higher level depend on tasks below them. 0sys runs lower levels first.

For example, installing packages must come before configuring services
that use them. Opening port 22 in the firewall must come before creating
a new user who needs to log in.

## Backends

A backend is what actually does the work. 0sys has three:

- **Ansible** — for system state: packages, services, users, files,
  firewall. Talks to the target over SSH.
- **Shell** — for raw commands. Runs directly on the target.
- **cloud-init** — generates user-data for VPS providers. Does not run
  anything.

You usually do not need to pick a backend. 0sys chooses based on the
task. You can override with `--backend ansible` if you want.

## Validation

Before building a plan, 0sys checks your configuration for common
mistakes:

- Firewall blocks SSH (you would lock yourself out).
- Package is both installed and removed.
- User with sudo has a login-disabled shell.
- Service needs a port that is not open.
- File destination is not an absolute path.

If any of these have severity `ERROR`, the plan is not built. Warnings
and info messages are shown but do not block.

## State and audit

Every `0sys apply` is recorded in two places:

- **State store** (`~/.local/share/0sys/state.db`) — a SQLite database
  with run and task history.
- **Audit log** (`~/.local/share/0sys/audit/*.jsonl`) — one file per
  run, with every action and secret redaction.

You can inspect runs with `0sys rollback --list`.