# Seed Network Security Skill

面向浙江大学《网络安全原理与实践》SEED 实验的一套独立技能仓库。它不是单个 prompt，也不是零散脚本集合，而是一组围绕“实验执行、证据留档、正式报告、可选展示工作台”组织起来的技能系统。

这套仓库当前以周子为 `3230106267` 的课程环境为第一落点完成收敛，但设计上已经拆出了足够清晰的定制面，便于迁移到自己的课程、实验平台或远端执行环境。

## 面向不同智能体的使用原则

这个仓库不是只给 Codex 用的。它同时考虑：

- Codex
- Claude Code
- OpenCode
- 其他会自行阅读仓库并理解说明的代码智能体

因此这里有一个总原则：

- 如果智能体支持“本地安装 skills 并在新会话自动加载”，优先安装并重启会话
- 如果智能体不支持 skill 安装，或者它本身更习惯直接读仓库，那就直接把这个仓库当作权威说明源使用

换句话说：

- `skills/` 是可安装的主线能力
- `README + docs/` 是跨智能体通用说明面

即使另一个智能体不理解 `$zju-seed-lab-runner` 这种触发方式，它只要能认真读仓库，也应该能按默认主线工作。

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

## 正常用户应当怎样用

这套仓库的正常使用方式应该非常自然：

1. 让智能体先安装 skills，如果它支持
2. 安装完成后重启会话
3. 重启后让它直接把“当前仓库”或“指定仓库”视为工作空间开始干活
4. 默认走主线，不先走 studio，不先讲很多话
5. 真正做完实验后，再决定要不要进入更完整的报告收尾或 studio 展示

这才是正常用户真正会怎么用它，而不是先理解一大堆内部工程细节。

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

### 0. 先判断你面前的智能体属于哪一类

#### 类型 A：支持安装本地 skills 的智能体

例如：

- Codex 一类支持从 `~/.codex/skills/` 加载技能的环境

推荐流程：

1. 执行 `python scripts/install_skills.py --validate`
2. 结束当前会话
3. 新开一个会话
4. 让智能体把当前仓库作为主线说明源开始工作

#### 类型 B：不依赖本地 skills 自动加载的智能体

例如：

- Claude Code
- OpenCode
- 其他更偏“直接阅读仓库”的智能体

推荐流程：

1. 不强求安装 skills
2. 直接让它阅读当前仓库的 `README.md` 和 `docs/`
3. 让它按默认主线模式开始工作

对这类智能体来说，这个仓库本身就是运行说明书。

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

## 默认主线行为

这个仓库希望智能体在“正常使用”时遵守下面这套默认行为。

### 1. 默认少说话，直接工作

如果用户让智能体：

- 查看当前仓库
- 查看指定仓库
- 开始做《网络安全原理与实践》作业
- 按默认方式开始

并且没有额外二次配置需求，那么默认行为应该是：

1. 先读当前仓库的 README 和相关 docs
2. 进入主线模式
3. 做材料审查
4. 做 preflight
5. 再进入实验执行
6. 归档 evidence
7. 汇报结果

除非遇到阻塞或缺配置，否则不要不断停下来问用户细枝末节。

### 2. 缺配置时才说话

如果智能体发现缺外部配置，它不应该自己胡乱补，也不应该跳过。

它应该只反馈三件事：

1. 缺了什么
2. 应该在哪里配置
3. 配好之后它下一步会做什么

也就是说，它的责任是“明确暴露外部阻塞”，而不是把外部环境问题伪装成内部完成。

### 3. 默认先主线，后展示

如果用户没有主动要求 studio / 统一工作台 / demo 展示：

- 默认不要一上来就走 studio
- 默认先把主线实验和留档做好

studio 的位置应该是：

- 主线已经完成之后
- 用户主动提出
- 或者智能体在收尾时把它作为一个可选补充向用户确认

### 4. 完整/详细报告请求的默认解释

如果用户明确提出：

- 生成最终完整报告
- 生成详细报告
- 把实验完整做完并交付

那么默认含义应该是：

1. 不是只把实验跑完
2. 而是实验做完后，自动继续进入报告完整流程
3. 也就是把 `report packager` 这条链一并做完

换句话说：

- “实验做完”不等于“交付做完”
- 用户说“完整/详细报告”时，应该默认继续跑正式报告收尾

## 给另一个智能体的推荐启动话术

下面这段话术可以直接发给另一个智能体。它不依赖某一家代理的专有触发语法，因此泛化性更高。

```text
请把当前仓库视为你的权威说明源，并先阅读 README.md。

如果你支持安装本地 skills，就先执行：
python scripts/install_skills.py --validate

安装成功后请提醒我重启会话；重启后继续。

如果你不支持 skill 安装，也不要紧，直接按 README 和 docs 作为说明源开始工作。

默认按主线模式处理《网络安全原理与实践》SEED 作业：
1. 先审查实验材料
2. 再做 preflight
3. 再执行实验
4. 收集 evidence 并留档

如果我说“最终完整报告”或“详细报告”，请在实验完成后自动继续完成正式报告流程，而不是停在实验执行结束。

除非缺配置或发生阻塞，否则尽量少说话，直接推进。

如果缺外部配置，只需要告诉我：
1. 缺什么
2. 去哪里配
3. 配完后你下一步做什么

studio / 统一工作台不是默认第一步，只有在主线做完后、我主动提出或你作为补充建议时再考虑。
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
