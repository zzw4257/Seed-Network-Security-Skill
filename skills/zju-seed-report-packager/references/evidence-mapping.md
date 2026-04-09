# Evidence Mapping

## Inputs

- Local DNS run:
  - `reports/lab4-dns-local/<run-id>/report.md`
  - `reports/lab4-dns-local/<run-id>/evidence/summary.json`
  - `reports/lab4-dns-local/<run-id>/evidence/*.log`
  - `reports/lab4-dns-local/<run-id>/evidence/generated/dns_spoof_lab.py`
- Remote DNS run:
  - `reports/lab4-dns-remote/<run-id>/report.md`
  - `reports/lab4-dns-remote/<run-id>/evidence/summary.json`
  - `reports/lab4-dns-remote/<run-id>/evidence/*.log`
  - `reports/lab4-dns-remote/<run-id>/evidence/generated/prepare_packets.py`
  - `reports/lab4-dns-remote/<run-id>/evidence/generated/attack.c`

## Extraction Rules

- Use `summary.json` for:
  - run status
  - analysis note titles and bodies
  - generated code list
  - high-level step inventory
- Use selected `.log` files for:
  - short factual snippets
  - dig outputs
  - cache grep results
  - authority IP discovery
- Prefer `STDOUT` excerpts over raw combined logs unless stderr itself proves something important.

## Report Placement

- Main body:
  - background and goals from lab Markdown
  - result narrative from real analysis notes
  - short key snippets from selected logs
  - screenshot slots
- Appendix:
  - generated code
  - evidence index
  - run source metadata

## Screenshot Mapping

- Keep screenshot slots task-oriented rather than step-oriented.
- Each slot needs:
  - stable filename
  - section binding
  - one-line capture subject
  - one-line explanation of why the screenshot matters
