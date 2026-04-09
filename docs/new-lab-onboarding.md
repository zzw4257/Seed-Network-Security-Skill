# 新实验接入流程

后续新增实验时，推荐按下面这条顺序推进。

## 总原则

先把主线做稳，再考虑报告层，再考虑展示层。

顺序固定为：

1. 实验材料
2. runner profile
3. preflight / full-run
4. report packager profile
5. 可选 studio 展示

## 1. 先准备实验材料

在仓库里放好：

1. 实验指导文档
2. `Labsetup`
3. 需要补的代码模板

建议结构仿照现有 `lab4-dns/`。

## 2. 先新增 runner manifest

位置：

```text
skills/zju-seed-lab-runner/assets/manifests/<new-profile>.yaml
```

最少要有：

- `profile_id`
- `doc_paths`
- `setup_path`
- `remote_workspace`
- `sync_paths`
- `materials_checks`
- `preflight_checks`
- `execution_steps`
- `evidence_commands`
- `report_sections`
- `quiz_prompts`

## 3. 先跑 preflight，再跑 full-run

```bash
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py preflight --profile <new-profile> --repo-root "$(pwd)"
python skills/zju-seed-lab-runner/scripts/seed_lab_runner.py full-run --profile <new-profile> --repo-root "$(pwd)"
```

只有当：

- 材料表正确
- 远端环境检查正确
- evidence 留档正确
- `reports/<profile>/<run-id>/` 结构稳定

才进入下一步。

## 4. 再新增 report packager profile

位置：

```text
skills/zju-seed-report-packager/assets/profiles/<new-report-profile>.json
```

只有当 runner 留档已经稳定时才做。

不要在实验还没跑顺之前就先写报告打包层。

## 5. 最后才考虑 studio 展示

`MASFactory` studio 是加分项，不是第一落点。

建议只在下面两种情况再接：

1. 已经想做 demo / 演示
2. 想把多个入口统一到一个本地工作台

## 6. 默认路线仍然是反向 SSH 直连

默认推荐：

```bash
ssh -i ~/.ssh/seed-way -p 2345 seed@localhost
```

只有在用户明确选 `seed-runner session mode` 时，才切到备选路线。
