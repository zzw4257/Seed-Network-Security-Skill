# 前提、环境与定制指南

这份文档回答两个问题：

1. 这套仓库默认依赖什么前提
2. 如果不是周子为这套课程环境，应该从哪里开始改

## 1. 默认前提

## 1.1 身份前提

当前主线 skill 默认服务：

- 周子为
- 学号 `3230106267`
- 浙江大学《网络安全原理与实践》

这部分主要体现在：

- `skills/zju-seed-lab-runner/SKILL.md`
- `skills/zju-seed-report-packager/SKILL.md`

## 1.2 远端实验环境前提

当前默认远端真相是：

- Proxmox 教学 VM
- Ubuntu 20.04
- reverse SSH 入口：
  - `ssh -i ~/.ssh/seed-way -p 2345 seed@localhost`
- 当前测试 VM sudo 密码：
  - `dees`
- 远端实验大量依赖 Docker / docker-compose

## 1.3 本地环境前提

默认本地环境应具备：

- `python`
- `ssh` / `scp`
- 若要编译正式报告：
  - `xelatex` 或 `latexmk`

如果要使用 studio 分支，还需要：

- Python 能运行 `.experiments/MASFactory/`

## 2. 可定制面

## 2.1 身份与课程定制

如果你不是为周子为这套环境服务，首先要改：

- `skills/zju-seed-lab-runner/SKILL.md`
- `skills/zju-seed-report-packager/SKILL.md`

建议改的内容：

- 姓名
- 学号
- 课程名
- 组织/学校名

## 2.2 远端连接定制

如果你的实验平台不是当前 reverse SSH：

优先改：

- `skills/zju-seed-lab-runner/references/environment.md`
- `skills/zju-seed-lab-runner/references/execution-modes.md`
- `skills/zju-seed-lab-runner/scripts/seed_runner_mode_helper.py`

你需要重新定义：

- 默认 SSH 入口
- 默认 OS / Python 假设
- sudo 约定
- 是否还用 Docker / Compose
- 是否还需要 `seed-runner` 作为备选路径

## 2.3 实验 profile 定制

这是最常见的扩展方式。

位置：

- `skills/zju-seed-lab-runner/assets/manifests/`
- `skills/zju-seed-report-packager/assets/profiles/`

这部分决定了：

- 实验文档在哪里
- Labsetup 在哪里
- 要执行哪些步骤
- 要采集哪些证据
- 报告章节怎么组织

## 2.4 报告模板定制

如果你不是要用当前这套 ZJU XeLaTeX 风格：

优先改：

- `lab4-dns/report-template/`
- `skills/zju-seed-report-packager/references/template-notes.md`
- `skills/zju-seed-report-packager/assets/profiles/`

你需要决定：

- 是保留 XeLaTeX 体系
- 还是改成另一套学校/课程模板
- 自动证据图在新模板里的版面和插图策略如何安排

## 2.5 展示层定制

如果你只是想用主线 skill，不一定要动 studio。

只有在这些情况下才建议改 studio：

- 你需要统一入口
- 你需要更强的 demo 形态
- 你想把 workflow、报告、手工收尾做成一个更产品化的界面

位置：

- `.experiments/MASFactory/applications/zju_seed_lab_studio/`

## 3. 定制顺序建议

最推荐的顺序是：

1. 先改身份和环境假设
2. 再接新的实验 profile
3. 跑通 runner
4. 再接 report packager
5. 最后再决定 studio 要不要跟着改

## 4. 什么不要先改

不建议一上来就改：

- studio 展示层
- 自动终端证据渲染细节
- 报告模板中的装饰性排版

原因很简单：

- 这些都依赖主线已经稳定
- 主线没跑通前，过早改它们只会增加复杂度

## 5. 如果你想把它改成自己的课程仓库

最小定制清单如下：

1. 改 `SKILL.md` 中的身份和课程说明
2. 改 runner 环境参考
3. 补一个新的 runner manifest
4. 准备该实验的样例材料和 sample run
5. 再补报告 profile

如果做到这一步，这个仓库就已经从“ZJU 当前课设版本”变成“你自己的网络安全实验 skill 仓库”了。
