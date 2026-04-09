# Manual Evidence UI

## Purpose

Provide a local browser UI so the user does not need to rename screenshots manually or edit JSON by hand.

## What It Does

- shows every expected screenshot slot
- previews the current manual image if present
- otherwise previews the current automatic terminal board
- accepts direct image upload into the correct slot filename
- stores extra notes and structured values in `manual-inputs.json`
- lets the user trigger a local PDF rebuild from the browser

## Command

```bash
python scripts/manual_evidence_ui.py \
  --package-root report-packages/lab4-dns-combined \
  --repo-root <repo> \
  --port 8765
```

- The UI will try the preferred port first and automatically move to the next available local port if that one is occupied.
- By default it opens the browser automatically.
- Use `--no-open-browser` only when you explicitly do not want that behavior.

Then use the printed URL, for example:

```text
http://127.0.0.1:8765
```

## Current Scope

- slot-by-slot image upload
- freeform notes
- freeform JSON values
- rebuild PDF
- automatic local port fallback
- automatic browser launch

## Intended Use

Use this after the lab has already been executed and the report package has already been built once. It is the human-in-the-loop finishing surface for the final polished PDF.

## Relation To The MASFactory Studio Branch

The mainline tool remains `manual_evidence_ui.py` itself.

If the experimental MASFactory studio surface is being used for demo or unified orchestration, the same UI can also be launched from:

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py \
  --workspace-root <repo> \
  --port 8877
```

That studio server does not replace the mainline report packager. It only wraps the same report package and manual UI into a single local web entry point.
