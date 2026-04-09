# 快速上手

这份文档面向第一次接手这个仓库的智能体或开发者，目标是最短路径确认“仓库结构正常、skills 可安装、至少一条链路可以立刻验证”。

## 1. 安装 skills

在仓库根目录执行：

```bash
python scripts/install_skills.py --validate
```

默认会把以下两个 skill 安装到 `~/.codex/skills/`：

- `zju-seed-lab-runner`
- `zju-seed-report-packager`

## 2. 运行本地验证

```bash
python scripts/validate_repo.py
```

它会做：

1. `quick_validate.py` 检查两个 skill
2. `py_compile` 检查 skill 脚本和 studio 脚本
3. 用仓库内示例归档对 `lab4-dns-combined` 跑一次 `inspect`

## 3. 不连 VM 时，优先测试报告链

这个仓库自带：

- `lab4-dns/` 实验材料
- `reports/lab4-dns-local/20260403-125920/`
- `reports/lab4-dns-remote/20260403-130805/`

所以你可以先直接验证报告打包：

```bash
python skills/zju-seed-report-packager/scripts/report_packager.py inspect --profile lab4-dns-combined --repo-root "$(pwd)"
python skills/zju-seed-report-packager/scripts/report_packager.py build --profile lab4-dns-combined --repo-root "$(pwd)"
python skills/zju-seed-report-packager/scripts/manual_evidence_ui.py --package-root report-packages/lab4-dns-combined --repo-root "$(pwd)" --port 8765
```

## 4. 连上教学 VM 后，再测试 runner

如果当前环境具备：

- reverse SSH 可达
- `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost` 可连接
- VM 中 Docker / Compose 正常

则可以继续：

```bash
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py preflight --profile lab4-dns-local --repo-root "$(pwd)"
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py full-run --profile lab4-dns-local --repo-root "$(pwd)"
```

## 5. 如果需要统一展示入口

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py --workspace-root "$(pwd)" --port 8877
```

这条入口适合：

- demo
- workflow 展示
- dashboard 聚合
- 从同一页启动 Manual UI

不适合：

- 替代主线 skill 做日常维护
- 作为新增实验的第一落点
