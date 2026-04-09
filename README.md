# Seed Network Security Skill

面向浙江大学《网络安全原理与实践》SEED 实验的一套可安装技能仓库，核心目标是把实验执行、证据留档、正式报告生成，以及可选的展示工作台整理成一套可以独立分发和复用的交付物。

这个仓库当前围绕周子为 `3230106267` 的课程环境收敛，默认支持：

- `zju-seed-lab-runner`
  - Proxmox / reverse-SSH / Docker SEED 实验自动执行与留档
- `zju-seed-report-packager`
  - XeLaTeX 正式报告包、自动终端证据板、手工截图 UI
- `zju_seed_lab_studio`
  - 基于 MASFactory 的可选展示增强分支，用于统一入口和图化演示

## 仓库内容

| 路径 | 说明 |
| --- | --- |
| `skills/zju-seed-lab-runner/` | 主线实验执行 skill |
| `skills/zju-seed-report-packager/` | 主线实验报告打包 skill |
| `lab4-dns/` | 当前随仓示例实验材料 |
| `reports/` | 当前随仓示例归档运行结果，可直接用于报告打包 smoke test |
| `.experiments/MASFactory/applications/zju_seed_lab_studio/` | 可选展示工作台 |
| `.experiments/MASFactory/masfactory/` | 为 studio 分支保留的最小 MASFactory 运行依赖 |
| `scripts/install_skills.py` | 安装仓库内 skills 到 `~/.codex/skills/` |
| `scripts/validate_repo.py` | 对 skills、脚本、示例 profile 做本地验证 |

## 快速开始

### 1. 安装 skills

```bash
python scripts/install_skills.py --validate
```

如果你只想安装某一个 skill：

```bash
python scripts/install_skills.py --skill zju-seed-lab-runner --validate
python scripts/install_skills.py --skill zju-seed-report-packager --validate
```

### 2. 验证仓库状态

```bash
python scripts/validate_repo.py
```

这一步会做三件事：

- 用 `quick_validate.py` 检查 skills 结构是否合法
- 对 skills 和 studio 的 Python 脚本做 `py_compile`
- 用仓库内自带的 `lab4-dns` 示例归档跑一次 `report_packager inspect`

### 3. 直接验证报告打包链

因为仓库内已经自带 sample archived runs，所以即使没有连 VM，也能先验证报告工具：

```bash
python skills/zju-seed-report-packager/scripts/report_packager.py inspect --profile lab4-dns-combined --repo-root "$(pwd)"
python skills/zju-seed-report-packager/scripts/report_packager.py build --profile lab4-dns-combined --repo-root "$(pwd)"
```

### 4. 如果教学 VM 可用，再验证实验执行链

```bash
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py preflight --profile lab4-dns-local --repo-root "$(pwd)"
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py full-run --profile lab4-dns-local --repo-root "$(pwd)"
```

## 默认路线

当前课程环境默认推荐：

- `Reverse-SSH direct mode`
  - `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`

备选路线：

- `seed-runner session mode`
  - 用于更通用的多机会话和挂载同步
  - 不会自动替代默认直连路线

## 当前随仓 profile

### Runner

- `lab4-dns-local`
- `lab4-dns-remote`

### Report Packager

- `lab4-dns-combined`

## 可选展示增强

如果要把这套技能以统一工作台的形式展示，可以使用 studio 分支：

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py --workspace-root "$(pwd)" --port 8877
```

它会提供：

- workflow 启动面板
- 最新 dashboard / PDF / Manual UI 链接
- 可选的独立 Manual UI 拉起
- 基于 MASFactory 的图化展示壳

## 文档导航

- [快速上手](docs/quickstart.md)
- [仓库结构说明](docs/repository-layout.md)
- [新实验接入流程](docs/new-lab-onboarding.md)
- [MASFactory Studio 说明](docs/masfactory-studio.md)

## 说明

- 主线能力以 `skills/` 为准。
- MASFactory studio 是可选展示分支，不替代主线 skill。
- 当前示例实验材料和 sample archived runs 都围绕 `lab4-dns`。
