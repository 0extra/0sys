# 0sys

A friendly server automation tool for beginner sysadmins.

## What is 0sys

0sys helps people who are just starting their journey as system
administrators. You do not need to know Ansible, Terraform, or any
other tool. You describe what you want in a simple configuration
file, and 0sys picks the right tool and does the work for you.

## Who is it for

- People who just learned `nano` and `cd`.
- People who want to set up their first VPS.
- People who are afraid to break something.
- People who want to understand what is happening.

## How it works

1. You run `0sys init`.
2. 0sys asks you simple questions.
3. 0sys generates a configuration file.
4. You run `0sys apply`.
5. 0sys explains every step it takes.

## Installation

```bash
curl -fsSL https://get.0sys.dev | bash
```

## Quick start

```bash
0sys init
0sys plan
0sys apply
```

## Documentation

See the [docs](docs/) directory.

## License

Apache License 2.0. See [LICENSE](LICENSE).