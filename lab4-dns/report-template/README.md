# 报告目录说明（Lab 2）

- 主文件：`lab2/report/lab2_report.tex`
- 样式文件：`lab2/report/zjureport.sty`
- 本地 LaTeX 依赖：`lab2/report/texmf-local/`
- TeX Live 依赖清单：`lab2/report/Texlivefile`
- 封面资源：`lab2/report/figures/zju_char.png`、`lab2/report/figures/zju_logo.png`
- 截图目录：`lab2/evidence/`

## 推荐编译方案（Docker + XeLaTeX）

宿主机若缺少完整 TeX 环境，建议沿用 Lab 1 的 Docker 编译方式：

```bash
sg docker -c "docker run --rm --entrypoint bash \
  -v $PWD:/workspace \
  -v /mnt/c/Windows/Fonts:/fonts:ro \
  -w /workspace/lab2/report \
  reitzig/texlive-base-xetex -lc '
    export TEXINPUTS=/workspace/lab2/report/texmf-local/tex//:;
    export TEXFONTMAPS=/workspace/lab2/report/texmf-local/fonts/misc/xetex/fontmapping//:;
    export OSFONTDIR=/fonts//;
    xelatex -interaction=nonstopmode lab2_report.tex &&
    xelatex -interaction=nonstopmode lab2_report.tex
  '"
```

说明：

- `/mnt/c/Windows/Fonts` 用作中文字体来源（适合 WSL 环境）
- `texmf-local/` 已 vendoring 了常用宏包关键文件，保证字体/版式稳定

