# 仓库结构说明

## 顶层

```text
Seed-Network-Security-Skill/
├── skills/
├── lab4-dns/
├── reports/
├── scripts/
├── docs/
└── .experiments/MASFactory/
```

## 1. `skills/`

这里是主线能力源代码。

### `skills/zju-seed-lab-runner/`

负责：

- 实验材料审查
- VM preflight
- Labsetup 同步
- 实验执行
- 证据留档
- Markdown 归档报告

### `skills/zju-seed-report-packager/`

负责：

- 从归档运行结果生成 XeLaTeX 报告包
- 自动终端证据板和故事板
- 手工截图 UI
- 本地 PDF 编译

## 2. `lab4-dns/`

这里是当前随仓样例实验材料。

包含：

- 本地攻击指导文档
- 远程攻击指导文档
- `Labsetup_DNS_Local `
- `Labsetup_DNS_Remote`
- 报告模板资源

它的作用不是“最终用户实验唯一目录”，而是给当前 skill profile 提供一个可复用样例和 smoke test 输入。

## 3. `reports/`

这里存放当前随仓的 sample archived runs。

用途：

- 让 `zju-seed-report-packager` 在没有连教学 VM 的情况下也能立刻测试
- 保留一组真实已完成的 `lab4-dns` local / remote 样例

当前保留：

- `reports/lab4-dns-local/20260403-125920/`
- `reports/lab4-dns-remote/20260403-130805/`

## 4. `scripts/`

仓库层脚本，而不是某个 skill 自己的执行脚本。

建议把所有“跨 skill 的安装、同步、验证动作”都放这里。

当前包含：

- `install_skills.py`
- `validate_repo.py`

## 5. `.experiments/MASFactory/`

这是可选展示增强，不是主线。

当前只保留两部分：

- `masfactory/`
  - studio 分支运行所需最小框架代码
- `applications/zju_seed_lab_studio/`
  - 把 runner / report packager 包成图化工作台

## 6. `docs/`

面向仓库使用者的顶层说明：

- 安装与验证
- 仓库结构
- 新实验接入
- studio 说明
