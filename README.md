# Seed Network Security Skill

面向浙江大学《网络安全原理与实践》SEED 实验的一套独立技能仓库。它不是单个 prompt，也不是零散脚本集合，而是一组围绕“实验执行、证据留档、正式报告、可选展示工作台”组织起来的技能系统。

这套仓库当前以周子为 `3230106267` 的课程环境为第一落点完成收敛，但设计上已经拆出了足够清晰的定制面，便于迁移到自己的课程、实验平台或远端执行环境。

## 这是什么

仓库当前包含三层能力：

1. 主线实验执行能力
   - `zju-seed-lab-runner`
   - 负责读实验材料、做 preflight、执行实验、收集证据、生成归档报告
2. 主线实验报告能力
   - `zju-seed-report-packager`
   - 负责把已完成运行结果重组为正式 XeLaTeX 报告、自动终端证据、手工截图收尾 UI
3. 可选展示增强能力
   - `zju_seed_lab_studio`
   - 基于 MASFactory 的展示壳，用于把 workflow、dashboard、PDF、Manual UI 统一到一个端口和一个交互面

如果只关心“把实验做完并留档”，前两层已经足够。第三层是可选展示面，不替代主线能力。

## 宏观架构

从高层看，这套 skill 系统是一个四层结构：

| 层 | 作用 | 典型产物 |
| --- | --- | --- |
| Knowledge Layer | 把课程约束、实验惯例、默认环境和 profile 描述固化为 skill + manifest | `SKILL.md`、`assets/manifests/`、`assets/profiles/` |
| Execution Layer | 把实验从“人肉步骤”转成可重复执行的非交互流程 | `seed_lab_runner.py` |
| Evidence & Report Layer | 把日志、代码、验证结果转成可展示、可提交、可补图的正式报告包 | `report_packager.py`、`manual_evidence_ui.py` |
| Experience Layer | 把主线能力再包成更适合 demo、统一入口和多阶段展示的工作台 | `zju_seed_lab_studio` |

更具体的智能体运行架构可看：

- [系统架构总览](docs/system-architecture.md)

## 运行路径总览

这套仓库不是只有一种运行方式，而是支持四种典型路径。

### 路径 A：主线直跑实验

适合：

- 已有教学 VM
- reverse SSH 已经打通
- 想最快执行实验并归档

核心链路：

```text
lab material -> runner preflight -> runner full-run -> reports/
```

### 路径 B：只跑报告链

适合：

- 没连上教学 VM
- 已经有 archived runs
- 想先验证技能或报告效果

核心链路：

```text
reports/ -> report packager -> report-packages/
```

### 路径 C：主线 + 手工收尾

适合：

- 实验已经完成
- 想补截图、补少量人工信息、重新编译正式 PDF

核心链路：

```text
report package -> manual evidence UI -> compiled PDF
```

### 路径 D：展示工作台

适合：

- 课程演示
- 想把 workflow / dashboard / PDF / Manual UI 放到同一个入口
- 想让另一个智能体从更“产品化”的入口开始看

核心链路：

```text
studio server -> workflow trigger / latest dashboard / latest PDF / manual UI
```

更细的运行模式和权衡见：

- [运行模式与斟酌项](docs/run-modes-and-tradeoffs.md)

## 前提条件

### 主线 runner 的默认前提

这套仓库当前对 ZJU SEED 环境的默认假设是：

- 本地用 `python`
- 教学 VM 用 Ubuntu 20.04
- 默认 SSH 入口：
  - `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`
- 教学 VM 中：
  - `docker` / `docker-compose` 可用
  - 实验大量依赖 Docker 容器
  - 习惯命令别名包括 `dcbuild` / `dcup` / `dcdown` / `dockps` / `docksh`
- 当前课程测试 VM 的 sudo 密码约定为：
  - `dees`

### report packager 的默认前提

- 已经有 `reports/<profile>/<run-id>/`
- 本地有可用 TeX 环境，优先 `latexmk -xelatex` / `xelatex`

### studio 的默认前提

- 主线 skills 已经可用
- 如果要跑 studio 展示壳，需要仓库内 `.experiments/MASFactory/` 保持完整

完整前提和可定制面见：

- [前提、环境与定制指南](docs/prerequisites-and-customization.md)

## 仓库内容

| 路径 | 说明 |
| --- | --- |
| `skills/zju-seed-lab-runner/` | 主线实验执行 skill |
| `skills/zju-seed-report-packager/` | 主线实验报告打包 skill |
| `lab4-dns/` | 当前随仓示例实验材料 |
| `reports/` | 当前随仓 sample archived runs，可直接用于报告链 smoke test |
| `.experiments/MASFactory/applications/zju_seed_lab_studio/` | 可选展示工作台 |
| `.experiments/MASFactory/masfactory/` | 为 studio 保留的最小 MASFactory 运行依赖 |
| `scripts/install_skills.py` | 安装仓库内 skills 到 `~/.codex/skills/` |
| `scripts/validate_repo.py` | 对 skills、脚本和 sample data 做本地验证 |

更细的结构说明见：

- [仓库结构说明](docs/repository-layout.md)

## 快速开始

### 1. 安装主线 skills

```bash
python scripts/install_skills.py --validate
```

如果只想安装某一个：

```bash
python scripts/install_skills.py --skill zju-seed-lab-runner --validate
python scripts/install_skills.py --skill zju-seed-report-packager --validate
```

### 2. 做一次仓库级验证

```bash
python scripts/validate_repo.py
```

它会：

- `quick_validate.py` 检查 skill 结构
- `py_compile` 检查主线和 studio 脚本
- 用随仓 `lab4-dns` archived runs 跑一次 `report_packager inspect`

### 3. 无 VM 时，先测试报告链

```bash
python skills/zju-seed-report-packager/scripts/report_packager.py inspect --profile lab4-dns-combined --repo-root "$(pwd)"
python skills/zju-seed-report-packager/scripts/report_packager.py build --profile lab4-dns-combined --repo-root "$(pwd)"
```

### 4. VM 可用时，再测试 runner

```bash
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py preflight --profile lab4-dns-local --repo-root "$(pwd)"
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py full-run --profile lab4-dns-local --repo-root "$(pwd)"
```

### 5. 如果要统一展示入口

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py --workspace-root "$(pwd)" --port 8877
```

## 如何定制成自己的版本

这套仓库不是只能服务当前课程环境。你可以在三个层面做定制：

### 1. 身份与环境定制

适合迁移到自己的课程、学号、实验机和默认路径。

主要调整：

- 两个 skill 的 `SKILL.md`
- runner 的 `references/environment.md`
- runner 的 `references/execution-modes.md`

### 2. 新实验接入

适合继续扩展新的 lab。

主要调整：

- `skills/zju-seed-lab-runner/assets/manifests/<new-profile>.yaml`
- `skills/zju-seed-report-packager/assets/profiles/<new-report-profile>.json`

### 3. 平台与交互定制

适合把这套系统移到另一种远程执行平台，或者换一种展示方式。

主要调整：

- runner 的 execution mode 约定
- report packager 的模板和证据映射
- studio 分支的工作台交互方式

完整迁移建议见：

- [前提、环境与定制指南](docs/prerequisites-and-customization.md)
- [新实验接入流程](docs/new-lab-onboarding.md)

## 当前随仓 profile

### Runner

- `lab4-dns-local`
- `lab4-dns-remote`

### Report Packager

- `lab4-dns-combined`

## 推荐阅读顺序

如果你是第一次接手这套仓库，建议按这个顺序：

1. [快速上手](docs/quickstart.md)
2. [系统架构总览](docs/system-architecture.md)
3. [运行模式与斟酌项](docs/run-modes-and-tradeoffs.md)
4. [前提、环境与定制指南](docs/prerequisites-and-customization.md)
5. [新实验接入流程](docs/new-lab-onboarding.md)
6. [MASFactory Studio 说明](docs/masfactory-studio.md)

## 关键边界

- 主线能力以 `skills/` 为准。
- studio 是可选展示增强，不替代主线 skill。
- 新实验永远优先落在 runner，再进入 report packager，最后才考虑 studio。
