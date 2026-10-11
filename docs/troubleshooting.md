# Troubleshooting

## `0sys doctor` reports missing components

Run `0sys doctor` first. It tells you exactly what is wrong.

### `ansible-playbook` not found

Install Ansible:

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

If you installed Ansible but the warning persists, check that it is in
`PATH`:

```bash
which ansible-playbook
```

## `0sys apply` fails with "SSH connection refused"

The target machine is not reachable on the given port.

- Check that the target is running.
- Check the IP address or hostname.
- Try SSH directly: `ssh user@host -p 22`.
- If you changed the SSH port, pass `--port`.

## `0sys apply` fails with "Permission denied"

The user does not have permission to run `sudo` on the target.

- Check that the user is in the `sudo` group: `ssh user@host 'groups'`.
- If not, log in as root and run:
  `usermod -aG sudo <user>`.

## `0sys apply` fails at the firewall task

The firewall rules conflict with your SSH session.

- Make sure port 22 is in `firewall.allow`.
- If you use a non-standard SSH port, add that port instead.
- Test on a throwaway VPS first.

## `0sys plan` shows "circular dependency detected"

Something in your config depends on itself. This is a bug; please open
an issue with the config that triggered it.

## Validation fails with FW001

The firewall is set to `deny` but port 22 is not in `allow`. This would
lock you out. Either:

- Add `22` to `firewall.allow`, or
- Set `firewall.default` to `allow`.

## Validation fails with PKG001

A package appears in both `packages.install` and `packages.remove`.
Remove it from one of the lists.

## Validation fails with USR002

A user has `sudo: true` but a login-disabled shell (like
`/usr/sbin/nologin`). Either:

- Change the shell to `/bin/bash`, or
- Set `sudo: false`.

## Cloud-init file looks wrong

Run with `--print` to inspect:

```bash
0sys cloud-init 0sys.yaml --print
```

Check that:

- The file starts with `#cloud-config`.
- `hostname`, `packages`, and `users` look correct.
- `runcmd` contains firewall and service lines.

## Logs and audit

0sys writes two kinds of logs.

Application log:

```bash
tail -f ~/.local/state/0sys/0sys.log
```

Audit log for a specific run:

```bash
ls ~/.local/share/0sys/audit/
cat ~/.local/share/0sys/audit/<file>.jsonl | jq .
```

## Getting help

1. Run `0sys doctor` and save the output.
2. Run `0sys plan <config>` and save the output.
3. Open an issue on GitHub with both.