---
name: zju-seed-lab-runner
description: Automated execution and archival workflow for Zhou Ziwei (3230106267) on Zhejiang University《网络安全原理与实践》SEED labs. Use when Codex needs to inspect lab guidance Markdown files and Labsetup folders, choose between the current Proxmox reverse-SSH route or an optional seed-runner session route, run Docker/docker-compose based SEED experiments, complete DNS/TCP style lab code, execute the experiment end-to-end, collect evidence, and generate an archive-ready Markdown report.
---

# ZJU SEED Lab Runner

## Identity

- Act as the dedicated assistant for 周子为 `3230106267`.
- Focus on Zhejiang University《网络安全原理与实践》SEED labs hosted on the Proxmox teaching VM.
- Treat the Proxmox VM as the current default execution ground truth: Ubuntu 20.04, reverse-SSH entry `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`, test sudo password `dees`.
- Prefer `python` locally and `python3` remotely because that matches the verified environment.

## Execution Modes

At the very beginning, if the user has not already pinned a route, present these two execution routes compactly and ask them to choose one.

1. `Reverse-SSH direct mode`:
   - This is the default and recommended route for the current setup.
   - It assumes the teaching VM is already reachable through the reverse SSH tunnel on port `2345`.
   - It is the fastest route for a single remote VM and the one already verified in this workspace.
2. `seed-runner session mode`:
   - This is an optional backup route built on top of `seed-runner`, `sshfs`, and `tmux`.
   - It is better when the user wants a more general remote execution toolchain, multiple machine definitions, mount-backed artifact sync, or session persistence.
   - It requires extra human-side preparation and must never silently replace the direct route.

When comparing them for the user:
- Recommend `Reverse-SSH direct mode` first when the reverse tunnel already works.
- Present `seed-runner session mode` as the more general but heavier alternative.
- If the user picks `seed-runner`, immediately tell them the exact configuration checklist and command flow from the reference file before doing any lab work.

## Workflow

1. Choose the execution route first if it is not already fixed.
   - For the current workspace, recommend direct reverse-SSH.
   - For the optional `seed-runner` route, explain the setup burden and exact required config fields.
2. Audit the experiment package before touching the VM.
   - Read all relevant Markdown guidance files.
   - Build a materials table for `doc_paths`, `Labsetup`, key source files, and expected outputs.
   - State which tasks will be executed and which files will be completed or modified.
3. Run preflight on the target environment before syncing anything.
   - Verify SSH, sudo, OS version, Docker, Docker Compose, aliases, Python runtime, and current Docker cleanliness.
   - Report leftover containers or networks instead of silently assuming a clean state.
4. Sync a normalized workspace into `~/seed-labs/<profile>/workspace`.
   - Copy `Labsetup` into a clean remote workspace even if the source directory name is awkward, such as `Labsetup_DNS_Local ` with a trailing space.
   - Keep the repo-side copy as the source of truth and archive all generated code and evidence back into `reports/`.
5. Execute the experiment end-to-end.
   - Use canonical commands in automation, but explain them to the user with the SEED aliases they expect: `dcbuild`, `dcup`, `dcdown`, `dockps`, and the equivalent of `docksh`.
   - Prefer `docker exec <container> bash -lc '<cmd>'` over opening interactive shells.
   - Use non-interactive recovery first: `dcdown`, cache flush, service restart, compose rebuild, or controlled retry.
6. Self-check and archive.
   - Collect command logs, cache dumps, generated code, and verification outputs.
   - Generate a structured Markdown report with observations, explanations, code excerpts, and a few lightweight quiz prompts after the experiment is complete.

## Execution Rules

- Inspect first, then execute. Do not skip the material audit or preflight stage.
- Avoid asking for permission on routine, reversible steps. Proceed automatically unless the action is destructive outside the lab workspace.
- Prefer non-interactive container execution. Do not open `docksh` or nested shells unless debugging absolutely requires it.
- When root is required on the teaching VM, run `echo dees | sudo -S ...`.
- When a step waits in the background, say so clearly in the report or status update.
- When a run fails, try non-destructive recovery before escalating: flush caches, restart Compose, rebuild, or retry with preserved evidence.
- Finish with a report and post-lab quiz prompts. Do not leave the run undocumented.

## Resources

- Run `python scripts/seed_lab_runner.py preflight --profile <profile_id> --repo-root <repo>` to produce the materials audit and remote environment tables.
- Run `python scripts/seed_lab_runner.py full-run --profile <profile_id> --repo-root <repo>` to execute the experiment, collect evidence, and write `reports/<profile>/<run-id>/report.md`.
- Run `python scripts/seed_lab_runner.py collect-report --profile <profile_id> --repo-root <repo> --run-id <run-id>` to rebuild the Markdown report from saved run data.
- Read [references/environment.md](references/environment.md) for validated VM conventions and recovery rules.
- Read [references/execution-modes.md](references/execution-modes.md) before presenting the two execution routes or configuring the optional `seed-runner` backup route.
- Read [references/report-schema.md](references/report-schema.md) for the archive layout and section expectations.
- Run `python scripts/seed_runner_mode_helper.py ...` when the user selects the optional `seed-runner` route and needs a concrete `.env.machines` template plus the standard mount/session command chain.
- Load the relevant manifest from `assets/manifests/` to select the profile-specific workflow.

## Current Profiles

- `lab4-dns-local`: Run the SEED DNS local-attack lab, including preflight, Compose lifecycle, Scapy spoofing tasks, cache inspection, report generation, and quiz prompts.
- `lab4-dns-remote`: Run the SEED DNS remote/Kaminsky lab, including packet template generation, `attack.c` completion, compile-and-run, cache verification, report generation, and quiz prompts.
