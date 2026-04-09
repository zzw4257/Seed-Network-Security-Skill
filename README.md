# Seed Network Security Skill

面向浙江大学《网络安全原理与实践》SEED 实验的一套技能仓库。

它的正常用途不是“让人先研究仓库结构”，而是：

1. 把仓库交给智能体
2. 智能体安装或加载其中的 skills
3. 重启会话
4. 让它按默认主线直接开始做实验

这个仓库当前围绕周子为 `3230106267` 的课程环境收敛，但设计上已经保留了清晰的定制面，便于后续迁移到别的课程、实验平台或远端执行环境。

## 先说怎么用

### 最自然的用法

把这个仓库交给另一个智能体，然后让它：

1. 用它自己的原生方式安装 `skills/` 里的 skills
2. 安装完成后重启会话
3. 重启后阅读当前仓库 `README.md`
4. 默认按主线模式开始做《网络安全原理与实践》作业

这里默认面向的是：

- Codex
- Claude Code
- OpenCode
- 其他支持 skill / prompt / repo-driven workflow 的代码智能体

重点是：

- 主路径应该是“智能体用它自己的原生方式安装 skill”
- 不是优先让用户手动跑我们仓库里的 Python 安装脚本

仓库里的 `scripts/install_skills.py` 只是兼容性兜底，不是首选入口。

### 给另一个智能体的最短启动话术

下面这段就是推荐的最短话术：

```text
请把当前仓库视为你的权威说明源。

先用你自己的原生方式安装这个仓库 `skills/` 目录下的 skills，然后重启会话。

重启后重新进入当前仓库，阅读 README.md，并按默认主线开始处理《网络安全原理与实践》SEED 作业：
1. 先审查实验材料
2. 再做 preflight
3. 再执行实验
4. 收集 evidence 并留档

如果我说“完整报告”或“详细报告”，请在实验完成后继续自动完成正式报告流程。

除非缺配置或发生真实阻塞，否则尽量少说话，直接推进。

如果缺外部配置，只告诉我：
1. 缺什么
2. 去哪里配
3. 配完后你下一步做什么

studio / 统一工作台不是默认第一步，只有主线做完后、我主动提出或你认为它适合作为补充展示时再进入。
```

## 默认主线行为

这个仓库希望智能体默认这样工作：

### 1. 默认先做主线

主线顺序是：

```text
材料审查 -> preflight -> 实验执行 -> evidence 留档 -> 归档报告
```

默认不要一上来就走：

- studio
- demo 壳
- 统一工作台
- 手工补图界面

这些都属于后置增强，不是默认起点。

### 2. 默认少说话，直接做

如果用户只是说：

- 看当前仓库
- 开始做作业
- 按默认方式开始

那么智能体应该默认：

1. 看 README 和必要文档
2. 找出当前实验材料
3. 直接进入主线流程

而不是先展开一大段解释，或者不断停下来确认普通步骤。

### 3. 缺配置时才反馈

如果缺的是外部配置，智能体不要自己瞎补，也不要把问题藏起来。

只需要反馈：

1. 缺什么
2. 去哪里配
3. 配完后下一步是什么

### 4. “完整报告 / 详细报告”默认意味着继续收尾

如果用户明确说：

- 最终完整报告
- 详细报告
- 完整交付

那默认不应停在实验执行结束，而应继续推进正式报告流程。

也就是说：

- 实验执行完成，不等于整个交付完成
- 明确要求完整报告时，应继续进入 report packager

## 这套仓库里有什么

仓库当前包含三层能力：

### 1. 主线实验执行能力

- `zju-seed-lab-runner`
- 负责：
  - 读实验材料
  - 做 preflight
  - 执行实验
  - 收集 evidence
  - 生成归档报告

### 2. 主线实验报告能力

- `zju-seed-report-packager`
- 负责：
  - 从 archived runs 生成正式 XeLaTeX 报告包
  - 自动终端证据板 / 故事板
  - 手工截图 UI
  - 本地编译 PDF

### 3. 可选展示增强能力

- `zju_seed_lab_studio`
- 负责：
  - workflow graph
  - dashboard
  - 本地 studio server
  - workflow / PDF / Manual UI 聚合展示

如果只关心“把实验做完并留档”，前两层已经够了。

## 仓库结构

| 路径 | 作用 |
| --- | --- |
| `skills/zju-seed-lab-runner/` | 主线实验执行 skill |
| `skills/zju-seed-report-packager/` | 主线实验报告打包 skill |
| `lab4-dns/` | 当前随仓示例实验材料 |
| `reports/` | 当前随仓 sample archived runs，可直接测试报告链 |
| `.experiments/MASFactory/applications/zju_seed_lab_studio/` | 可选展示工作台 |
| `.experiments/MASFactory/masfactory/` | studio 所需最小 MASFactory 运行依赖 |

## 当前默认环境

当前主线默认面向的是这套环境：

- 本地用 `python`
- 教学 VM 用 Ubuntu 20.04
- 默认 SSH 入口：
  - `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`
- VM 中：
  - `docker`
  - `docker-compose`
- 常用别名：
  - `dcbuild`
  - `dcup`
  - `dcdown`
  - `dockps`
  - `docksh`
- 当前测试 VM sudo 密码约定：
  - `dees`

## 当前随仓 profile

### Runner

- `lab4-dns-local`
- `lab4-dns-remote`

### Report Packager

- `lab4-dns-combined`

## 如果你现在就要测试

### 不连教学 VM

先直接测试报告链：

```bash
python skills/zju-seed-report-packager/scripts/report_packager.py inspect --profile lab4-dns-combined --repo-root "$(pwd)"
python skills/zju-seed-report-packager/scripts/report_packager.py build --profile lab4-dns-combined --repo-root "$(pwd)"
```

### 教学 VM 可用

再测试 runner：

```bash
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py preflight --profile lab4-dns-local --repo-root "$(pwd)"
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py full-run --profile lab4-dns-local --repo-root "$(pwd)"
```

### 想做展示

最后再看 studio：

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py --workspace-root "$(pwd)" --port 8877
```

## 定制自己的版本

如果你想把它迁移成自己的课程技能仓库，优先改这三块：

1. `skills/*/SKILL.md`
   - 身份
   - 课程
   - 默认行为契约
2. `skills/zju-seed-lab-runner/assets/manifests/`
   - 新实验 profile
3. `skills/zju-seed-report-packager/assets/profiles/`
   - 新实验报告 profile

更细的迁移与架构说明见：

- [系统架构总览](docs/system-architecture.md)
- [运行模式与斟酌项](docs/run-modes-and-tradeoffs.md)
- [前提、环境与定制指南](docs/prerequisites-and-customization.md)
- [新实验接入流程](docs/new-lab-onboarding.md)
- [MASFactory Studio 说明](docs/masfactory-studio.md)

## 最后强调一次边界

- 真正的默认运行契约，以 `skills/` 下的 skill 本体为准
- README 负责给人和跨代理入口一个足够清晰的起点
- studio 不是默认第一步
- 新实验永远优先落在 runner，再进入 report packager，最后才考虑 studio
