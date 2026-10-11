# 0sys examples

Ready-to-use configuration files for common scenarios.

## Files

| File | Purpose |
|---|---|
| `01-web-server.yaml` | nginx with HTTPS-ready firewall (ports 22, 80, 443) |
| `02-vpn-server.yaml` | WireGuard VPN with IP forwarding enabled |
| `03-docker-host.yaml` | Docker and docker-compose for container workloads |
| `04-ci-runner.yaml` | Minimal host for running CI jobs in containers |
| `05-dev-environment.yaml` | General purpose development box |

## Usage

Copy an example and adjust it to your needs:

```bash
cp examples/01-web-server.yaml my-server.yaml
$EDITOR my-server.yaml
0sys plan my-server.yaml
0sys apply my-server.yaml
```

## Generate your own

Run the interactive wizard to build a custom config:

```bash
0sys init
```