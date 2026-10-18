# Security considerations

## Secrets

0sys attempts to redact sensitive data (passwords, tokens, private keys)
before writing to logs or the SQLite state database. However, the primary
defense against leaking secrets is not putting them in the YAML config.

Use environment variables or external secret providers where possible.

## Shell commands

The `commands` section in a 0sys configuration is executed directly on the
target server with `shell=True`. This means the YAML configuration is
treated as executable code with the same privileges as the SSH user.

Only run configurations you trust.

## SSH host keys

By default, 0sys uses `StrictHostKeyChecking=accept-new` for the first
connection to a new host and then pins the key in a local `known_hosts`
file. This protects against man-in-the-middle attacks but trusts the first
connection.

If you have an out-of-band way to verify the server's host key, use
`--strict-host-key` on the `apply` command to enforce strict checking
without auto-accepting new keys.