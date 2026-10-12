# Positioning

0sys is often compared to Ansible, Terraform, and cloud-init. This page
explains what each of them does and where 0sys fits.

## Short version

0sys is a **planner and validator** that uses other tools as backends.
It is not a competitor to Ansible or Terraform. It is a layer in front
of them.

## What Ansible does

Ansible is a configuration management tool. You write YAML playbooks that
describe the state of a server, and Ansible applies them over SSH.

**Strengths:**

- Hundreds of built-in modules
- Idempotent by design
- Works on any Linux, macOS, and Windows target
- Massive community and documentation

**Weaknesses for beginners:**

- Playbooks are verbose. A simple web server takes 40+ lines.
- You need to know which module to use for each task.
- Error messages assume you already understand the underlying system.
- Nothing explains *why* a step is needed.

## What Terraform does

Terraform creates infrastructure: VPS instances, networks, DNS records,
load balancers. You write `.tf` files in HCL, run `terraform apply`, and
Terraform talks to cloud provider APIs.

**Strengths:**

- Declarative, plan/apply cycle
- Rich provider ecosystem
- State file tracks everything

**Weaknesses for beginners:**

- Does not configure the operating system inside a server
- State file management is error-prone
- HCL syntax is another language to learn

## What cloud-init does

cloud-init runs on first boot of a VPS. You provide a `user-data` file,
and cloud-init configures the server once.

**Strengths:**

- Supported by every major VPS provider
- Works before you can SSH in

**Weaknesses:**

- Runs only once. Changing something later is painful.
- Limited modules compared to Ansible
- No plan/apply cycle

## Where 0sys fits

0sys reads one YAML file and decides what to do with each section.

| Section | What it needs | What 0sys does |
|---|---|---|
| `packages`, `services`, `users`, `firewall`, `files` | Configure an existing server | Generates Ansible playbook, runs `ansible-runner` |
| `infrastructure` | Create a VPS | Generates Terraform HCL, you run `terraform apply` |
| `proxy` | Deploy 0TPE in Docker | Generates Ansible playbook with docker-compose |
| `commands` | Raw shell | Runs directly, no idempotency |

The result: **one config language, five ways to execute it**.

## Why not just use Ansible?

Three reasons.

**1. You don't have to know Ansible.** 0sys validates your config,
picks the right modules, and explains what it does. You learn Ansible
as a side effect if you want to.

**2. Validation catches beginner mistakes.** 0sys refuses to plan a
config that would lock you out of your server, install and remove the
same package, or create a user with `sudo` and a disabled login shell.
Ansible would happily try and fail at the third task.

**3. It teaches.** `0sys explain` and `0sys explain-term` translate
the plan into plain English. `0sys tips` gives practical advice.
`0sys rollback` shows what can and cannot be undone.

## Why not just use Terraform?

Terraform is great at creating infrastructure but does nothing inside
the VM. You still need a config management tool after `terraform apply`.

0sys does both: one config file can create the VPS **and** configure it.

## Why not just use cloud-init?

cloud-init is one-shot. If you want to change something later, you have
to SSH in or rebuild the server. 0sys uses cloud-init as one output
format, but the same config can be applied to a running server via
Ansible.

## When 0sys is not the right tool

- **Large fleets (100+ servers)** — Ansible with proper inventory,
  roles, and CI is more appropriate.
- **Complex infrastructure** — Terraform modules, workspaces, and
  remote state are more mature.
- **Kubernetes-first workloads** — Helm, Kustomize, and ArgoCD are the
  right tools.
- **Immutable infrastructure** — NixOS, Flatcar, or Talos do this
  better as a primary strategy.

0sys is a good fit for **1–20 servers** managed by one or two people,
where the goal is clarity and safety, not scale.