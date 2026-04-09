# MASFactory Studio 说明

`zju_seed_lab_studio` 是这个仓库里的可选展示增强分支。

## 定位

它不是主线执行引擎，也不替代主线 skill。

它做的事情是：

- 把主线 runner / report packager 包成图化工作流
- 导出 `summary.json`、`graph.json`、`dashboard.html`
- 提供一个本地 studio server，把 workflow、dashboard、PDF、Manual UI 聚合到一个端口

## 入口

### 直接跑一次 graph

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/main.py --workflow-mode report_only --graph-mode static
```

### 启动 studio server

```bash
python .experiments/MASFactory/applications/zju_seed_lab_studio/studio_server.py --workspace-root "$(pwd)" --port 8877
```

## 适合什么

- 课程 demo
- 展示自动化工作流
- 把 dashboard / PDF / Manual UI 汇总到一个页面
- 在已有主线能力之上提供更好看的交互入口

## 不适合什么

- 作为新增实验的第一实现面
- 替代 `skills/` 下主线能力做维护
- 在主线 runner / report packager 还没稳定前提前接入

## 现在已经能做什么

- 从页面发起 workflow
- 轮询 job 输出
- 查看最新 dashboard
- 打开最新 PDF
- 独立拉起最新 package 对应的 Manual UI
- 自动处理本地端口冲突
