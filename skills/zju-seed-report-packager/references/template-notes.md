# Template Notes

## Base Template Source

- Reuse `lab4-dns/report-template/` as the visual baseline.
- Copy these items into each generated package:
  - `zjureport.sty`
  - `texmf-local/`
  - `figures/`
- Do not modify `lab2_report.tex` or `lab3_report.tex` in place.
- Generate a fresh `lab4_dns_report.tex` for the new package.

## Local Compilation

- Prefer local `latexmk -xelatex`.
- Verified local tools:
  - `xelatex`
  - `latexmk`
- Use the package-local TeX resources by exporting:
  - `TEXINPUTS=<report-dir>/texmf-local/tex//:`
  - `TEXFONTMAPS=<report-dir>/texmf-local/fonts/misc/xetex/fontmapping//:`

## Placeholder Strategy

- Every manual screenshot slot must work in two states:
  - real image exists: render the image
  - image missing: render a framed placeholder with filename and capture hint
- Keep placeholder naming stable so users can fill screenshots without editing TeX.

## Style Expectations

- Preserve ZJU cover, Chinese academic tone, table of contents, and formal section numbering.
- Keep the main body evidence-driven and readable.
- Put exhaustive code and log material into appendices or evidence snippets.
