# Terminal Shot Engine

## Purpose

Generate presentation-grade terminal evidence automatically from real run logs so the report can contain richer and more coherent visual proof than isolated screenshots.

## What It Uses

- `summary.json` step inventory for user-facing commands and result previews
- selected evidence log snippets for stable outputs
- generated code previews for code-oriented panes
- Playwright headless Chromium as a rendering backend
- Pillow contact-sheet assembly for report-wide evidence overview

## Design

- Render two evidence layers:
  - `terminal-boards/`: one task-level main evidence board per key task
  - `storyboards/`: one continuous frame storyboard per key task
- Boards use multi-pane terminal workspaces with role-specific panes.
- Storyboards use step-labeled frames to show time progression inside a task.
- The report prefers:
  1. manual screenshot in `evidence/manual/`
  2. auto terminal board in `evidence/auto/terminal-boards/`
  3. placeholder box
- Storyboards are inserted as secondary evidence after the main board.
- A contact sheet is generated in `evidence/auto/verification/contact-sheet.png`.

## Commands

- Full package build with boards + storyboards:
  - `python scripts/report_packager.py build --profile lab4-dns-combined --repo-root <repo>`
- Only regenerate terminal boards:
  - `python scripts/report_packager.py render-auto-shots --profile lab4-dns-combined --repo-root <repo>`
- Only regenerate storyboards:
  - `python scripts/report_packager.py render-storyboards --profile lab4-dns-combined --repo-root <repo>`
- Regenerate all evidence and verification outputs:
  - `python scripts/report_packager.py verify-evidence --profile lab4-dns-combined --repo-root <repo>`

## Current Output

- Main boards are written into `evidence/auto/terminal-boards/`
- Storyboards are written into `evidence/auto/storyboards/`
- Verification reports and contact sheet are written into `evidence/auto/verification/`

## Limits

- These images are evidence renderings, not literal OS screenshots.
- They aim to look natural and readable, but they are still reconstructed from logs.
- They are optimized for static PDF presentation, not for perfect OS-level fidelity.
- Very dynamic shell states such as inline editors, progress spinners, mouse interactions, or interactive TUIs are not yet reconstructed faithfully.
