# ZJU SEED Lab Studio

This is an **experimental MASFactory integration branch** for the existing ZJU SEED lab toolchain.

It does **not** replace the current `zju-seed-lab-runner` or `zju-seed-report-packager`.  
Instead, it wraps the current capabilities into a MASFactory graph so they can be:

- previewed as a multi-agent workflow
- traced in MASFactory Visualizer
- evolved toward Vibe Graphing style orchestration later

## What It Wraps

- `zju-seed-lab-runner`
- `zju-seed-report-packager`
- `manual_evidence_ui.py`
- MASFactory graph serialization and a local dashboard artifact for each run

## Current Workflow Modes

- `report_only`
  - inspect or package an existing report flow
  - optional manual evidence UI launch
  - optional evidence verification
- `package_review`
  - build the report package
  - optionally launch the manual evidence UI
  - optionally run evidence verification
- `full_lab`
  - reserved for future deeper execution integration
  - preflight and full-run hooks are already wired, but should only be used when the remote route is ready

## Graph Modes

- `static`
  - use the hand-authored MASFactory graph that wraps the existing tools
  - safest current mode
- `vibegraph`
  - use MASFactory `VibeGraph` to generate the orchestration structure from natural-language build instructions
  - intended as the next-step design surface for this branch
  - requires OpenAI-compatible model credentials

## Run Artifacts

Every invocation now writes a timestamped run directory under:

```bash
.experiments/MASFactory/applications/zju_seed_lab_studio/runs/<timestamp>/
```

Each run directory contains:

- `summary.json`
  - full stage-by-stage status, commands, outputs, package paths, UI URL, and verification status
- `graph.json`
  - MASFactory Visualizer-shape serialization of the current graph
- `dashboard.html`
  - a local presentation page that summarizes the workflow, outputs, graph lane, and stage transcripts
- `README.md`
  - minimal artifact index for the run

Convenience copies are also refreshed:

- `runs/latest.json`
- `runs/latest-graph.json`
- `runs/latest-dashboard.html`

## Studio Server

If you want a single local entry point for demo use, you can launch the studio server:

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py \
  --workspace-root /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体 \
  --port 8877
```

It will:

- auto-pick another port if the preferred one is occupied
- render a control panel for `report_only` / `package_review` / `full_lab`
- start workflow runs from the page
- poll the active job output
- show links to the latest dashboard, latest PDF, and latest manual UI
- embed the latest generated dashboard in the page itself
- independently launch the latest package's manual evidence UI from the same page

## Run

From the workspace root:

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/main.py \
  --workspace-root /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体 \
  --workflow-mode report_only \
  --open-dashboard
```

For the VibeGraph route:

```bash
OPENAI_API_KEY=... \
python .experiments/MASFactory/applications/zju_seed_lab_studio/main.py \
  --workspace-root /Users/zzw4257/Documents/ZJU_archieve/08-AI之路/2026-4-3-基于openwork的网安原智能体 \
  --workflow-mode report_only \
  --graph-mode vibegraph
```

## Notes

- This branch is intentionally isolated under `.experiments/MASFactory/`.
- It is meant to improve orchestration visibility and demo interaction, not to disturb the existing mainline tools.
- The hand-authored static graph is the stable path today; the VibeGraph mode is the design-forward path for future orchestration evolution.
- `package_review` now behaves like a real review lane: it packages the report, preserves the manual UI launch option, and exports a browsable dashboard for demo use.
