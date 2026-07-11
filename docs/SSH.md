# SSH and remote file transfer

Seven uses the operating system's OpenSSH clients rather than maintaining a second SSH implementation. Tools:

- `ssh_status` reports client paths and enforced policy; it does not claim a remote connection.
- `ssh_run` executes one noninteractive remote command and returns the real exit code, bounded stdout/stderr, timeout and terminated process IDs.
- `ssh_copy_to` and `ssh_copy_from` transfer one file using scp's SFTP mode.

All operations enforce `BatchMode=yes`, `StrictHostKeyChecking=yes`, and `PasswordAuthentication=no`. Authentication comes from the user's OpenSSH agent, normal SSH configuration, or an explicit identity-file path. Seven does not accept, encrypt, persist, place on a command line, or audit a password.

## Host trust

The host must already have a verified entry in the user's default `known_hosts`, or the caller can provide a separate `known_hosts_file`. Seven never uses `AutoAddPolicy`, `accept-new`, or `StrictHostKeyChecking=no`. Provision host keys out of band and compare fingerprints with the server owner; blindly saving `ssh-keyscan` output does not authenticate a server.

Example:

```text
ssh_run(host="server.example", username="seven", command="uname -a", identity_file="~/.ssh/id_ed25519")
```

Host and username accept conservative DNS/IPv4/SSH-config-alias characters. Use `~/.ssh/config` aliases for more complex routing or IPv6 targets. Ports are bounded to 1–65535. Command timeout is bounded to 10 minutes and transfer timeout to 30 minutes. Timeout cleanup owns and terminates the complete local OpenSSH process tree.

Outputs are capped at 50,000 characters for stdout and 20,000 for stderr with an explicit truncation flag. Remote commands themselves can expose secrets in output or command text; Seven's general audit redaction handles recognizable credential fields/patterns but is not a universal data-loss-prevention system.

## L4 authority and limits

This is intentionally unrestricted remote command authority once the user's SSH credentials and host trust permit it. Seven does not apply the v3 blocklist: substring blocklists are bypassable and falsely imply safety. Remote account permissions, sudo policy, OpenSSH configuration, and the calling MCP/client's consent are the real boundaries.

Transfers force modern SFTP mode and cover individual files only; directory recursion, sync, interactive shells, port forwarding, agent setup, password prompts, and persistent connection claims are not supported by these tools. A missing client, rejected host key, failed authentication, nonzero remote exit, incomplete transfer, or timeout is returned as failure.

## Legacy disposition

The v3 Paramiko manager auto-accepted unknown host keys, attempted local reversible password storage, silently removed passwords from saved server records, and used a bypassable destructive-command substring list. It could therefore claim a configured server while losing its credential and trust a machine it had never authenticated. Those behaviors were rejected rather than carried forward.
