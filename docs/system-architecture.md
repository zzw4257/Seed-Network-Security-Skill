# 系统架构总览

这份文档回答的不是“命令怎么敲”，而是“这套技能系统在技术上是怎样分层、怎样协同、为什么这样设计”。

## 1. 设计目标

这套仓库服务的是一种很具体但又很常见的场景：

- 远端实验环境不是本地开发机
- 实验流程长、重复且容易在细节上出错
- 既要自动化执行，又要形成可提交的证据链和正式报告
- 最后还希望对外展示时，有统一的入口和更好的叙事感

因此系统目标不是做“一个脚本”，而是拆成一组职责明确的能力层。

## 2. 四层结构

## Layer 1: Skill Knowledge Layer

这一层负责把“实验世界的约束”写成技能知识。

包含：

- `SKILL.md`
- `references/`
- `assets/manifests/`
- `assets/profiles/`

作用：

- 明确身份、默认环境、执行纪律
- 把实验 profile、文档路径、Labsetup、证据命令写成机器可复用的结构
- 避免智能体每次都从零理解课程环境

这一层回答的问题是：

- 我是谁
- 这个实验世界默认长什么样
- 当前有哪些实验 profile
- 哪些路径、别名、容器规则是默认真相

## Layer 2: Execution Layer

这一层负责把“实验步骤”变成可重复执行的流程。

核心是：

- `skills/zju-seed-lab-runner/scripts/seed_lab_runner.py`

它不直接关心正式 PDF 排版，而是关心：

- 材料是否齐全
- 教学 VM 是否可达
- Docker / Compose 是否正常
- Labsetup 是否同步正确
- 每个任务如何执行
- 证据如何归档到 `reports/`

这一层回答的问题是：

- 实验能不能跑
- 能不能稳定重跑
- 结果能不能以 structured archive 的形式留下来

## Layer 3: Evidence & Report Layer

这一层负责把“归档的运行结果”转成“正式提交材料”。

核心是：

- `skills/zju-seed-report-packager/scripts/report_packager.py`
- `skills/zju-seed-report-packager/scripts/manual_evidence_ui.py`

它不重新做实验，而是把已有 evidence 重组为：

- XeLaTeX 报告包
- 自动终端证据板 / 故事板
- 截图槽位
- 手工补图界面
- 最终 PDF

这一层回答的问题是：

- 这次实验能不能从“日志目录”提升为“正式报告”
- 自动证据和人工补证怎样结合
- 最终交付怎样更完整、更稳定

## Layer 4: Experience Layer

这一层是可选的体验和展示包装层。

核心是：

- `.experiments/MASFactory/applications/zju_seed_lab_studio/`

它不替代前两层或前三层，而是把它们包成：

- workflow graph
- dashboard
- 本地 studio server
- 统一入口

这一层回答的问题是：

- 如何把这套系统更直观地展示给人看
- 如何让 workflow、PDF、Manual UI 从一个端口统一进入
- 如何把自动化系统以更像“产品”的方式展示

## 3. 智能体视角下的职责分工

虽然主线使用时通常还是一个核心智能体在行动，但逻辑上可以把它看成四种角色：

### 1. Orchestrator

负责判断当前该走哪条路径：

- 是不是先做 preflight
- 是不是已经可以只跑报告链
- 是不是要进入 studio 展示层

### 2. Lab Executor

负责把实验真正跑起来：

- SSH / 远端环境
- Docker / Compose
- Labsetup 同步
- 任务执行

### 3. Evidence Archivist

负责把原始命令、输出、代码、验证结果按结构化方式保留下来。

### 4. Report Composer

负责把结构化 evidence 转成正式报告和展示材料。

注意：

- 在当前实现里，这些职责不一定由四个独立 agent 实例承担
- 但从架构上，四者已经被分成了四个不同的能力层
- 这就是后续继续演进成更多 agent surface 的基础

## 4. 为什么不把所有能力揉成一个 skill

原因很简单：

1. 实验执行和报告生产的节奏不同
2. 实验执行需要连真实环境，报告生产可以离线做
3. 展示层不是每次都需要
4. 让每一层单独稳定，比一个大而全的技能更可维护

所以当前仓库选择的是：

- 主线两 skill
- 一个可选 studio 分支

而不是：

- 一个超级大 skill 包办所有事情

## 5. 当前架构的稳定边界

目前最稳定的是：

- `zju-seed-lab-runner`
- `zju-seed-report-packager`

目前更偏增强性质的是：

- `zju_seed_lab_studio`

因此后续继续发展时，推荐顺序始终是：

1. 先稳主线实验执行
2. 再稳主线报告
3. 最后再增强展示层
