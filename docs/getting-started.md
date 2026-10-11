# Getting started

This guide takes you from zero to a working server in about ten minutes.

## What you need

- A computer running Linux or macOS
- Python 3.11 or newer
- A target machine: your laptop, a virtual machine, or a VPS
- SSH access to the target (if it is not your local machine)

You do not need to know Ansible, Docker, or any other tool.

## Install 0sys

With pipx:

```bash
pipx install zerosys
```

If you do not have pipx:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

## Check the environment

```bash
0sys doctor
```

This tells you what is missing. If `ansible-playbook` shows a warning,
install Ansible:

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

## Create your first config

The interactive wizard asks simple questions:

```bash
0sys init
```

You will be asked:

1. What to call the server
2. Which timezone to use
3. Which preset fits your use case
4. Whether to create an admin user
5. Which ports to open
6. Which services to install
7. Which extra packages you want
8. A final review

Answer honestly. There are no wrong answers. When finished, `0sys.yaml`
appears in the current directory.

## Review the plan

```bash
0sys plan 0sys.yaml
```

You will see a tree of tasks grouped by level. Tasks at the same level
can run in parallel.

## Read the explanations

```bash
0sys explain 0sys.yaml
```

This prints each step in plain English. If something looks wrong here,
fix the config before applying.

## Try a dry run

```bash
0sys check 0sys.yaml
```

Nothing changes on the target. This is the safest way to see what would
happen.

## Apply for real

```bash
0sys apply 0sys.yaml
```

If the target is not your local machine:

```bash
0sys apply 0sys.yaml --host 192.0.2.10 --user admin --ssh-key ~/.ssh/id_ed25519
```

You will be asked to type `yes` before anything changes. After that,
0sys runs each task and prints the result.

## Verify

```bash
0sys rollback --list
```

This shows the history of runs. The most recent should be `success`.

## Next steps

- Read [concepts.md](concepts.md) to understand how 0sys thinks.
- Read [config-reference.md](config-reference.md) to learn every field.
- Read [backends.md](backends.md) to see how 0sys talks to servers.