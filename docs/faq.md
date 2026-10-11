# FAQ

## What is 0sys, in one sentence?

A tool that turns a simple YAML file into a configured server, with
explanations and safety checks for people who are new to system
administration.

## Is 0sys a replacement for Ansible?

No. 0sys uses Ansible under the hood for most tasks. You do not need to
know Ansible to use 0sys, but Ansible does the actual work.

## Is 0sys a replacement for Terraform?

Not yet. Terraform support is planned but not implemented. 0sys
currently configures existing servers; it does not create them.

## Can 0sys create a VPS?

Not directly. But you can generate a cloud-init file with
`0sys cloud-init` and paste it into your VPS provider's user-data field.
The server will configure itself on first boot.

## Which Linux distributions are supported?

0sys works on any Linux distribution with Python 3.11 or newer. For
remote targets, Ansible supports Debian, Ubuntu, Fedora, RHEL, CentOS,
Rocky, AlmaLinux, Arch, Alpine, and openSUSE.

macOS is supported for the controller. It is not a typical target.

## Does 0sys need root on the target?

For most operations, yes. 0sys connects over SSH and uses `sudo` or
Ansible's `become`. The initial user must have sudo privileges.

## Is it safe to run `0sys apply` twice?

Yes, for most tasks. 0sys is designed to be idempotent: running the
same config again should not change anything. Exceptions are raw shell
commands, which run every time unless marked `once`.

## Where does 0sys store data?

- State database: `~/.local/share/0sys/state.db`
- Audit logs: `~/.local/share/0sys/audit/*.jsonl`
- Log file: `~/.local/state/0sys/0sys.log`

On macOS, replace `~/.local/share` with `~/Library/Application Support`
and `~/.local/state` with `~/Library/Logs`. 0sys uses `platformdirs`,
so the actual paths match platform conventions.

## Can I roll back a run?

Partial support. `0sys rollback` lists past runs and shows their tasks.
Automatic rollback of arbitrary changes is not implemented because some
actions cannot be reversed safely (for example, `apt install` leaves
files behind even after `apt remove`).

## What if I lock myself out?

The validator checks for this before applying. If `firewall.default` is
`deny` and port 22 is not in `firewall.allow`, 0sys refuses to build a
plan. You cannot accidentally lock yourself out through 0sys.

If you lock yourself out another way, use your VPS provider's rescue
console.

## Does 0sys send my data anywhere?

No. 0sys runs entirely on your machine and the target you specify. It
does not phone home, does not collect telemetry, and does not send
anything to the maintainers.

## Can I use it in a commercial project?

Yes. 0sys is licensed under Apache-2.0, which permits commercial use.

## How do I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Where do I report bugs?

Open an issue on [GitHub](https://github.com/0extra/0sys/issues). Use
the bug report template and include your `0sys --version` output.