# Report Schema

Use this structure for every archived run:

## 1. 实验总结

- State the profile, run ID, target VM, and overall outcome.
- Summarize the main attack or lab objective and the final observed result.

## 2. 材料审查表

- List every guidance document, Labsetup directory, and key starter file.
- Mark each item as present, missing, or auto-generated.

## 3. 前置环境表

- Record SSH connectivity, OS version, Docker/Compose status, alias availability, sudo validation, Python runtime, and Docker cleanliness.
- Record the chosen execution route:
  - `reverse-ssh-direct`
  - `seed-runner-session`

## 4. 逐任务执行记录

- Describe each major step in order.
- Show the human-facing explanation, the actual command family, the important output, and the evidence log path.

## 5. 结果与证据

- Capture cache dumps, dig outputs, compile logs, generated packet templates, or other proof artifacts.
- Link every key observation back to an evidence file under `evidence/`.
- When using `seed-runner`, also capture:
  - `mount_id`
  - `session_id`
  - key `log_file_local` paths
  - any artifacts synchronized through the mounted shared directory

## 6. 实验成果留档

- List all generated or completed code files.
- Include a short explanation of what each code artifact changed or accomplished.

## 7. 思考题与解释

- Answer the lab questions that naturally arise from the observed results.
- Skip the section if there is nothing meaningful to explain.

## 8. 附加 Quiz

- Add a few lightweight follow-up questions only after the experiment is complete and the report is written.
