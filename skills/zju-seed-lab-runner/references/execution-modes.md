# Execution Modes

Use this file when the user has not already fixed an execution route and the runner must introduce the current default path plus the optional generalized backup path.

## Mode A: Reverse-SSH Direct Mode

This is the current mainline and should be recommended first for this workspace.

- Entry: `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`
- Best for:
  - one already-prepared teaching VM
  - the current Proxmox reverse-SSH setup
  - fastest time-to-execution
  - minimal extra preparation
- Strengths:
  - already validated in this workspace
  - lowest setup overhead
  - easiest to reason about for a single machine
- Weaknesses:
  - tied to the reverse tunnel being alive
  - less general for multi-machine orchestration
  - remote session persistence and mount abstraction are manual

## Mode B: seed-runner Session Mode

This is an optional backup route and should never silently replace Mode A.

- Tool repo: `https://github.com/ElysiaFollower/SEEDRunner`
- Best for:
  - multiple machine definitions
  - mount-backed artifact synchronization
  - tmux-managed remote shell sessions
  - a more general remote execution surface beyond the current reverse tunnel
- Strengths:
  - explicit machine catalog
  - session lifecycle via CLI
  - local shared directory sync through `sshfs`
  - clearer session-level execution records
- Weaknesses:
  - heavier initial setup
  - requires remote-to-local SSH reachability
  - requires `tmux` and `sshfs` on the experiment VM
  - depends on `.env.machines` being correct before use

## seed-runner Minimum Checklist

These are the practical minimum requirements condensed from the external tool's own setup expectations plus the course environment realities:

1. Local machine and experiment VM can authenticate to each other via SSH public keys.
2. The experiment user on the VM, for example `seed`, has passwordless `sudo`.
3. The user can provide:
   - local host reachable from the VM
   - local SSH port
   - remote VM host
   - remote VM port
   - remote VM user
   - remote VM private key path
4. The experiment VM already has:
   - `tmux`
   - `sshfs`
   - `ssh`
5. The local machine has installed `seed-runner` with:
   - `python3 -m pip install -e ".[dev]"`

## `.env.machines` Fields To Explain

The user must know these exact knobs:

```dotenv
SEED_RUNNER_LOCAL_HOST=<local-host-reachable-from-vm>
SEED_RUNNER_LOCAL_SSH_PORT=<local-ssh-port>
# Optional:
# SEED_RUNNER_LOCAL_USER=<local-user-for-remote-to-local-ssh>
# SEED_RUNNER_REMOTE_TO_LOCAL_KEY=<key-on-vm-used-to-ssh-back-to-local>

MACHINE_vm-seed-01_HOST=<remote-vm-host>
MACHINE_vm-seed-01_PORT=<remote-vm-port>
MACHINE_vm-seed-01_USER=<remote-vm-user>
MACHINE_vm-seed-01_KEY=<local-private-key-path-for-remote-vm>
```

## Standard `seed-runner` Command Chain

Once configured, the normal flow is:

```bash
seed-runner mount create \
  --machine vm-seed-01 \
  --local-dir ./artifacts

seed-runner session create \
  --machine vm-seed-01 \
  --mount-id <mount-id> \
  --name <session-name>

seed-runner session exec \
  --session <session-id> \
  --cmd "<command>"

seed-runner session status --session <session-id>

seed-runner session destroy --session <session-id>
seed-runner mount destroy --mount-id <mount-id>
```

## Report Implication

Whichever mode is chosen, keep the report contract stable:

- archive outputs under `reports/`
- preserve generated code and evidence
- when using `seed-runner`, include `mount_id`, `session_id`, and key `log_file_local` references in the final report appendix or evidence section
