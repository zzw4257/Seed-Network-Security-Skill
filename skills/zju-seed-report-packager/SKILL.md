---
name: zju-seed-report-packager
description: Build polished Zhejiang University XeLaTeX experiment report packages for Zhou Ziwei (3230106267) from completed SEED lab evidence, report templates, and later manual screenshots. Use when Codex needs to turn existing archived runs under the `reports/` tree, together with `summary.json`, evidence logs, generated code, and `report-template` assets, into a complete report package, screenshot placeholder set, shot list, and compiled PDF, especially for `lab4-dns` and future ZJU SEED lab reports.
---

# ZJU SEED Report Packager

## Identity

- Serve 周子为 `3230106267` on Zhejiang University《网络安全原理实践》实验报告 production.
- Treat the job as report packaging, not experiment execution.
- Default to a refined Zhejiang University XeLaTeX report that is faithful to real evidence and pleasant for later manual screenshot补证.

## Default Operating Contract

- This skill is the mainline formal-deliverable surface once archived evidence already exists.
- Do not treat report generation as a brainstorming task by default. If the user asks for the final report, the complete report, or the detailed report, move directly into inspect -> build -> compile rather than stopping after a plan.
- Operate quietly and directly. Only interrupt when an external prerequisite is missing, such as TeX not being available or required archived runs not existing.
- If blocked by missing external prerequisites, report only:
  1. what is missing
  2. where it must be configured or provided
  3. what the next step will be once it is fixed
- Manual screenshot upload and studio workbench usage are post-mainline finishing surfaces. Do not make them the default first step unless the user explicitly asks for them or the automatic report package has already been produced and the next obvious step is human补证.

## Workflow

1. Inspect the finished lab evidence before writing anything.
   - Read the chosen `summary.json`, generated code, evidence logs, and experiment guidance Markdown.
   - Confirm the selected runs are `completed`.
2. Map evidence into a report package.
   - Reuse `lab4-dns/report-template` assets and ZJU style files.
   - Build a clean package root with `report/`, `evidence/auto/`, and `evidence/manual/`.
3. Write the report for humans, not for the machine log.
   - Summarize real verified outcomes.
   - Keep full step-by-step logs out of the main body unless they prove a key point.
   - Place high-value command snippets, code, and evidence references where they support the narrative.
4. Design screenshot补拍 intentionally.
   - Every critical screenshot slot must have a stable filename, a clear caption, and a short capture instruction.
   - If the screenshot does not exist yet, show an elegant placeholder box in the PDF.
5. Compile locally.
   - Prefer local `latexmk -xelatex` or `xelatex`.
   - Keep Docker TeX only as fallback guidance, not the primary path.

## Delivery Contract

- The default finished state for this skill is a compiled formal report package, not merely an inspected evidence table.
- If the user explicitly requests a final / complete / detailed report, continue through:
  1. run selection
  2. evidence mapping
  3. package generation
  4. PDF compilation
- Do not default to opening Manual UI or studio after build unless:
  - the user explicitly asks for it
  - or the automatic report is already built and the next missing part is clearly manual screenshot completion

## Rules

- Do not rerun the lab just to write the report.
- Prefer real evidence over expected textbook outcomes when the two differ.
- Keep the report body polished and task-level; move raw logs and exhaustive traces into appendices or snippets.
- Always generate `SHOT_LIST.md` together with the TeX package.
- Always preserve a stable package layout so users can补图 and recompile without touching the script.
- Treat `build` as the default path when the user wants the real deliverable. Treat `inspect` as a preview or diagnostic path, not the normal final stop.

## Resources

- Run `python scripts/report_packager.py inspect --profile <profile_id> --repo-root <repo>` to preview run selection, evidence completeness, section mapping, and screenshot slots.
- Run `python scripts/report_packager.py build --profile <profile_id> --repo-root <repo>` to generate the full report package and compile the PDF.
- Run `python scripts/report_packager.py render-auto-shots --profile <profile_id> --repo-root <repo>` to regenerate terminal boards from real logs without rebuilding the whole package.
- Run `python scripts/report_packager.py render-storyboards --profile <profile_id> --repo-root <repo>` to regenerate task-level continuous storyboards.
- Run `python scripts/report_packager.py verify-evidence --profile <profile_id> --repo-root <repo>` to regenerate boards, storyboards, verification reports, contact sheet, and fallback checks.
- Run `python scripts/report_packager.py compile --package-root <package-root>` to recompile after manual screenshots are added.
- Run `python scripts/manual_evidence_ui.py --package-root <package-root> --repo-root <repo> --port 8765` to launch a local browser UI for uploading slot images, filling hard-to-fetch values, auto-selecting an available local port if needed, opening the browser, and recompiling the PDF.
- Read [references/template-notes.md](references/template-notes.md) for template reuse and local TeX rules.
- Read [references/evidence-mapping.md](references/evidence-mapping.md) for how logs, generated code, and screenshot slots map into the report.
- Read [references/terminal-shots.md](references/terminal-shots.md) for the automatic terminal screenshot engine and its limits.
- Load the relevant JSON profile from `assets/profiles/`.

## Current Profile

- `lab4-dns-combined`: Build one combined “实验四：DNS 攻击实验（本地与远程）” report package from the completed local and remote DNS runs.
