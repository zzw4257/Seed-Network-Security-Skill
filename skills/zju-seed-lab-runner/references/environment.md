# Environment Notes

## Identity And Defaults

- Serve 周子为 `3230106267` on Zhejiang University《网络安全原理与实践》SEED labs.
- Use the Proxmox teaching VM as the default execution target.
- Default route: reverse-SSH direct mode via `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`.
- Optional backup route: `seed-runner` session mode when the user explicitly chooses the more general tmux + sshfs orchestration toolchain.
- Treat `dees` as the test-only sudo password for this VM.
- Use `python` locally and `python3` remotely unless a profile proves otherwise.

## Verified VM Facts

- Remote OS: `Ubuntu 20.04.6 LTS`.
- `docker-compose` exists at `/usr/local/bin/docker-compose`.
- `python3` exists remotely; plain `python` is not guaranteed remotely.
- `dcbuild`, `dcup`, `dcdown`, `dockps`, and `docksh` are defined in the remote interactive shell.
- Current Docker state may contain leftover networks even when no containers are running. Diagnose first; do not assume a pristine state.

## Execution Conventions

### Mode A: Reverse-SSH Direct Mode

- Run automation with canonical commands for reliability:
  - `docker-compose build`
  - `docker-compose up -d`
  - `docker-compose down --remove-orphans`
  - `docker exec <container> bash -lc '<cmd>'`
- Explain those actions to the user with the SEED aliases they already know:
  - `dcbuild`
  - `dcup`
  - `dcdown`
  - `dockps`
  - `docksh <id>`
- Prefer non-interactive execution everywhere. Avoid entering a shell inside a container unless debugging requires it.

### Mode B: seed-runner Session Mode

- Treat this as an explicit backup route, not the silent default.
- Only use it when the user chooses it or when the direct reverse-SSH path is unavailable and the user agrees to the extra setup burden.
- Core expectations:
  - local shared directory mounted to the VM through `sshfs`
  - remote execution through `seed-runner session exec`
  - multi-terminal state managed via `tmux`
- The user-facing summary must always explain:
  - why Mode A is still the recommended fast path for the current workspace
  - what extra configuration Mode B requires
  - that Mode B is better for generalized multi-machine or persistent session workflows

## Recovery Order

1. Capture the failing output and write it into evidence.
2. Try the narrowest safe recovery:
   - `rndc flush`
   - service restart
   - `docker exec ...` retry
3. If the environment still looks inconsistent, run `docker-compose down --remove-orphans` and then rebuild or restart.
4. Remove leftover networks only if they block Compose recreation and no dependent containers remain.
5. Stop only on true system blockers such as broken SSH, broken Docker daemon, or missing core lab files.
