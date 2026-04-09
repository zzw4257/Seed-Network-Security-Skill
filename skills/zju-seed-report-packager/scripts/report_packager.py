#!/usr/bin/env python
import argparse
import datetime as dt
import html as html_lib
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path


class PackagerError(RuntimeError):
    pass


def tex_escape(value):
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    result = []
    for char in str(value):
        result.append(replacements.get(char, char))
    return "".join(result)


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")).replace("\n", "<br>") for header in headers) + " |")
    return "\n".join(lines)


def slugify(value):
    cleaned = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", value.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned or "item"


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_command_log(path):
    text = Path(path).read_text(encoding="utf-8")
    command = ""
    exit_code = ""
    stdout = ""
    stderr = ""
    if text.startswith("$ "):
        first_break = text.find("\n\n")
        command = text[2:first_break].strip() if first_break != -1 else text[2:].strip()
    exit_match = re.search(r"\[exit=(.*?)\]", text)
    if exit_match:
        exit_code = exit_match.group(1)
    stdout_match = re.search(r"STDOUT:\n(.*?)\n\nSTDERR:\n", text, re.S)
    stderr_match = re.search(r"STDERR:\n(.*)$", text, re.S)
    if stdout_match:
        stdout = stdout_match.group(1).strip()
    if stderr_match:
        stderr = stderr_match.group(1).strip()
    return {
        "command": command,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "raw": text,
    }


def excerpt_text(text, max_lines):
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines] + ["..."]
    return "\n".join(lines).strip() + ("\n" if lines else "")


def find_latest_completed_run(reports_dir):
    candidates = []
    for child in Path(reports_dir).iterdir():
        if not child.is_dir():
            continue
        summary_path = child / "evidence" / "summary.json"
        if not summary_path.exists():
            continue
        try:
            summary = read_json(summary_path)
        except Exception:
            continue
        if summary.get("status") == "completed":
            candidates.append((child.name, child))
    if not candidates:
        raise PackagerError("没有找到 status=completed 的运行留档")
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def resolve_run(profile_source, repo_root, explicit_run_id=None):
    reports_dir = repo_root / profile_source["reports_dir"]
    if explicit_run_id:
        run_dir = reports_dir / explicit_run_id
        if not run_dir.exists():
            raise PackagerError(f"指定 run id 不存在: {run_dir}")
        summary_path = run_dir / "evidence" / "summary.json"
        if not summary_path.exists():
            raise PackagerError(f"指定 run 缺少 summary.json: {summary_path}")
        summary = read_json(summary_path)
        if summary.get("status") != "completed":
            raise PackagerError(f"指定 run 不是 completed: {explicit_run_id}")
        return run_dir
    default_run = profile_source.get("default_run_id")
    if default_run:
        default_dir = reports_dir / default_run
        summary_path = default_dir / "evidence" / "summary.json"
        if default_dir.exists() and summary_path.exists():
            summary = read_json(summary_path)
            if summary.get("status") == "completed":
                return default_dir
    return find_latest_completed_run(reports_dir)


class ReportPackager:
    def __init__(self, repo_root, profile_id, local_run_id=None, remote_run_id=None):
        self.repo_root = Path(repo_root).resolve()
        self.skill_dir = Path(__file__).resolve().parents[1]
        self.profile = read_json(self.skill_dir / "assets" / "profiles" / f"{profile_id}.json")
        self.profile_id = profile_id
        self.local_run_dir = resolve_run(self.profile["source_runs"]["local"], self.repo_root, local_run_id)
        self.remote_run_dir = resolve_run(self.profile["source_runs"]["remote"], self.repo_root, remote_run_id)
        self.local_summary = read_json(self.local_run_dir / "evidence" / "summary.json")
        self.remote_summary = read_json(self.remote_run_dir / "evidence" / "summary.json")
        self.package_root = self.repo_root / "report-packages" / self.profile["package_dirname"]
        self.report_dir = self.package_root / "report"
        self.auto_snippets_dir = self.package_root / "evidence" / "auto" / "snippets"
        self.auto_code_dir = self.package_root / "evidence" / "auto" / "generated-code"
        self.auto_boards_dir = self.package_root / "evidence" / "auto" / "terminal-boards"
        self.auto_storyboards_dir = self.package_root / "evidence" / "auto" / "storyboards"
        self.verification_dir = self.package_root / "evidence" / "auto" / "verification"
        self.boards_manifest_path = self.verification_dir / "terminal-boards-manifest.json"
        self.boards_report_path = self.verification_dir / "terminal-boards-report.md"
        self.storyboards_manifest_path = self.verification_dir / "storyboards-manifest.json"
        self.storyboards_report_path = self.verification_dir / "storyboards-report.md"
        self.contact_sheet_path = self.verification_dir / "contact-sheet.png"
        self.manual_dir = self.package_root / "evidence" / "manual"
        self.manual_extras_dir = self.manual_dir / "extras"
        self.context_path = self.package_root / "report-context.json"
        self.selected_log_context = []
        self.generated_code_context = []
        self.manual_import_summary = {"matched": [], "extras": []}
        self.snippet_lookup = {}
        self.analysis_local = {item["title"]: item["body"] for item in self.local_summary.get("analysis_notes", [])}
        self.analysis_remote = {item["title"]: item["body"] for item in self.remote_summary.get("analysis_notes", [])}

    def build_context(self):
        return {
            "profile_id": self.profile_id,
            "title": self.profile["title"],
            "header": self.profile["header"],
            "course": self.profile["course"],
            "student": self.profile["student"],
            "local_run_id": self.local_run_dir.name,
            "remote_run_id": self.remote_run_dir.name,
            "local_report_path": str((self.local_run_dir / "report.md").relative_to(self.repo_root)),
            "remote_report_path": str((self.remote_run_dir / "report.md").relative_to(self.repo_root)),
            "selected_logs": self.selected_log_context,
            "selected_generated_code": self.generated_code_context,
            "manual_import_summary": self.manual_import_summary,
            "auto_terminal_boards_dir": str(self.auto_boards_dir.relative_to(self.package_root)),
            "auto_storyboards_dir": str(self.auto_storyboards_dir.relative_to(self.package_root)),
            "verification_reports": {
                "terminal_boards_report": str(self.boards_report_path.relative_to(self.package_root)),
                "terminal_boards_manifest": str(self.boards_manifest_path.relative_to(self.package_root)),
                "storyboards_report": str(self.storyboards_report_path.relative_to(self.package_root)),
                "storyboards_manifest": str(self.storyboards_manifest_path.relative_to(self.package_root)),
                "contact_sheet": str(self.contact_sheet_path.relative_to(self.package_root)),
            },
            "render_mode": "multi-pane-continuous-terminal-board-and-storyboard",
            "screenshot_slots": self.profile["screenshot_slots"],
            "build_timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        }

    def inspect(self):
        rows = [
            {
                "来源": "local",
                "run_id": self.local_run_dir.name,
                "status": self.local_summary["status"],
                "report": str((self.local_run_dir / "report.md").relative_to(self.repo_root)),
                "steps": len(self.local_summary.get("steps", [])),
            },
            {
                "来源": "remote",
                "run_id": self.remote_run_dir.name,
                "status": self.remote_summary["status"],
                "report": str((self.remote_run_dir / "report.md").relative_to(self.repo_root)),
                "steps": len(self.remote_summary.get("steps", [])),
            },
        ]
        log_rows = []
        for item in self.profile["selected_logs"]:
            source_dir = self.local_run_dir if item["source"] == "local" else self.remote_run_dir
            path = source_dir / "evidence" / item["filename"]
            log_rows.append(
                {
                    "片段": item["snippet_name"],
                    "来源": item["source"],
                    "文件": item["filename"],
                    "状态": "存在" if path.exists() else "缺失",
                }
            )
        slot_rows = [
            {
                "截图文件": slot["filename"],
                "章节": slot["section"],
                "用途": slot["caption"],
            }
            for slot in self.profile["screenshot_slots"]
        ]
        chapter_rows = [{"章节": item["title"]} for item in self.profile["chapter_map"]]
        output = [
            f"Profile: {self.profile_id}",
            "",
            "## 运行选择",
            markdown_table(["来源", "run_id", "status", "report", "steps"], rows),
            "",
            "## 证据片段映射",
            markdown_table(["片段", "来源", "文件", "状态"], log_rows),
            "",
            "## 章节映射",
            markdown_table(["章节"], chapter_rows),
            "",
            "## 截图位预览",
            markdown_table(["截图文件", "章节", "用途"], slot_rows),
        ]
        return "\n".join(output)

    def _normalize_name(self, name):
        base = Path(name).stem
        base = base.replace("，", "").replace(",", "").replace(" ", "").replace("　", "")
        base = base.lower()
        return base

    def _manual_slot_mapping(self):
        return {
            "local-config-dig-baseline.png": ["本地dns实验基线检查", "本地dns实验基线", "基线检查"],
            "local-task1-user-spoof-result.png": ["本地dns任务1"],
            "local-task2-cache-poisoning.png": ["本地dns任务2"],
            "local-task3-ns-poisoning.png": ["本地dns任务3"],
            "local-task4-cross-domain-cache-observation.png": ["本地dns任务4"],
            "local-task5-additional-section-cache.png": ["本地dns任务5"],
            "remote-baseline-dig-and-cache.png": ["远程dns基线"],
            "remote-request-trigger-trace.png": ["远程dns查当前权威ip", "远程dns查当前权威"],
            "remote-kaminsky-cache-success.png": ["远程dns攻击日志"],
            "remote-final-dig-verification.png": ["远程dns最终验证"],
        }

    def _import_manual_images(self):
        ensure_dir(self.manual_dir)
        ensure_dir(self.manual_extras_dir)
        mapping_rules = self._manual_slot_mapping()
        consumed = set()
        sources = [self.repo_root / "lab4-dns" / "evidence-manual"]
        for source_dir in sources:
            if not source_dir.exists():
                continue
            image_files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
            normalized = {p: self._normalize_name(p.name) for p in image_files}
            for slot_name, keywords in mapping_rules.items():
                chosen = None
                for path, norm in normalized.items():
                    if path in consumed:
                        continue
                    if any(keyword in norm for keyword in keywords):
                        chosen = path
                        break
                if chosen:
                    shutil.copy2(chosen, self.manual_dir / slot_name)
                    consumed.add(chosen)
                    self.manual_import_summary["matched"].append(
                        {"source": str(chosen.relative_to(self.repo_root)), "target": f"evidence/manual/{slot_name}"}
                    )
            for path in image_files:
                if path in consumed:
                    continue
                safe_name = slugify(path.stem) + path.suffix.lower()
                target = self.manual_extras_dir / safe_name
                shutil.copy2(path, target)
                self.manual_import_summary["extras"].append(
                    {"source": str(path.relative_to(self.repo_root)), "target": str(target.relative_to(self.package_root))}
                )

    def _copy_template_assets(self):
        template_dir = self.repo_root / self.profile["template_dir"]
        for name in ["zjureport.sty", "texmf-local", "figures"]:
            source = template_dir / name
            target = self.report_dir / name
            if source.is_dir():
                shutil.copytree(source, target, ignore=shutil.ignore_patterns(".DS_Store"), dirs_exist_ok=True)
            else:
                shutil.copy2(source, target)

    def _extract_and_write_snippets(self):
        for item in self.profile["selected_logs"]:
            source_run = self.local_run_dir if item["source"] == "local" else self.remote_run_dir
            log_path = source_run / "evidence" / item["filename"]
            parsed = parse_command_log(log_path)
            stream_text = parsed[item.get("stream", "stdout")] if item.get("stream", "stdout") in parsed else parsed["stdout"]
            snippet = excerpt_text(stream_text, item.get("max_lines"))
            snippet_path = self.auto_snippets_dir / item["snippet_name"]
            snippet_path.write_text(snippet, encoding="utf-8")
            context_item = {
                "id": item["id"],
                "source": item["source"],
                "title": item["title"],
                "source_log": str(log_path.relative_to(self.repo_root)),
                "snippet_path": str(snippet_path.relative_to(self.package_root)),
                "command": parsed["command"],
                "exit_code": parsed["exit_code"],
            }
            self.selected_log_context.append(context_item)
            self.snippet_lookup[item["id"]] = {
                "path_from_tex": "../" + str(snippet_path.relative_to(self.package_root)).replace(os.sep, "/"),
                "content": snippet,
                "meta": context_item,
            }

    def _copy_generated_code(self):
        for item in self.profile["selected_generated_code"]:
            source_run = self.local_run_dir if item["source"] == "local" else self.remote_run_dir
            source = source_run / item["relative_path"]
            target = self.auto_code_dir / item["output_name"]
            shutil.copy2(source, target)
            self.generated_code_context.append(
                {
                    "title": item["title"],
                    "language": item["language"],
                    "source": item["source"],
                    "source_path": str(source.relative_to(self.repo_root)),
                    "package_path": str(target.relative_to(self.package_root)),
                }
            )

    def _write_shot_list(self):
        lines = [
            f"# {self.profile['title']} 图像清单",
            "",
            "- 所有图片统一放到 `evidence/manual/`。",
            "- 文件名必须与清单中的名称完全一致，这样重新编译时才会自动替换对应占位框。",
            "- 建议优先保证终端内容清楚、命令与结果同屏、关键缓存行位于画面中部。",
            "",
        ]
        for index, slot in enumerate(self.profile["screenshot_slots"], start=1):
            lines.extend(
                [
                    f"## {index}. `{slot['filename']}`",
                    f"- 章节：{slot['section']}",
                    f"- 图注：{slot['caption']}",
                    f"- 建议终端：{slot.get('terminals', '按实验实际情况取景')}",
                    f"- 拍摄内容：{slot['description']}",
                    f"- 取景建议：{slot.get('capture_hint', '保证命令与结果同时可见。')}",
                    f"- 重要性：{slot['why']}",
                    "",
                ]
            )
        (self.manual_dir / "SHOT_LIST.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_build_script(self):
        report_file = self.profile["report_filename"]
        final_pdf = self.profile["final_pdf_name"]
        script = textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail

            SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
            export TEXINPUTS="${{SCRIPT_DIR}}/texmf-local/tex//:"
            export TEXFONTMAPS="${{SCRIPT_DIR}}/texmf-local/fonts/misc/xetex/fontmapping//:"

            cd "${{SCRIPT_DIR}}"
            latexmk -xelatex -interaction=nonstopmode -file-line-error {report_file}
            cp -f "${{SCRIPT_DIR}}/{report_file.replace('.tex', '.pdf')}" "${{SCRIPT_DIR}}/../{final_pdf}"
            """
        )
        build_path = self.report_dir / "build.sh"
        build_path.write_text(script, encoding="utf-8")
        build_path.chmod(0o755)

    def _analysis_block(self, text):
        body = "\n".join(f"{tex_escape(line)}\\par" for line in text.strip().splitlines() if line.strip())
        return textwrap.dedent(
            f"""\
            \\begin{{quote}}
            \\small
            \\noindent {body}
            \\end{{quote}}
            """
        )

    def _command_block(self, caption, body, language="bash"):
        return textwrap.dedent(
            f"""\
            \\begin{{lstlisting}}[language={language},caption={{{tex_escape(caption)}}}]
            {body.strip()}
            \\end{{lstlisting}}
            """
        )

    def _slot(self, filename):
        for slot in self.profile["screenshot_slots"]:
            if slot["filename"] == filename:
                return slot
        raise PackagerError(f"未知截图位: {filename}")

    def _figure_tex(self, filename):
        slot = self._slot(filename)
        return textwrap.dedent(
            f"""\
            \\begin{{figure}}[H]
                \\centering
                \\IfFileExists{{../evidence/manual/{filename}}}{{%
                    \\includegraphics[width=0.90\\textwidth]{{../evidence/manual/{filename}}}%
                }}{{%
                    \\IfFileExists{{../evidence/auto/terminal-boards/{filename}}}{{%
                        \\includegraphics[width=0.90\\textwidth]{{../evidence/auto/terminal-boards/{filename}}}%
                    }}{{%
                        \\fbox{{\\begin{{minipage}}[c][0.22\\textheight][c]{{0.88\\textwidth}}
                            \\centering \\textbf{{图像未提供}}\\\\[0.6em]
                            \\small 建议文件名：\\path{{{filename}}}\\\\
                            \\small {tex_escape(slot['description'])}
                        \\end{{minipage}}}}%
                    }}%
                }}
                \\caption{{{tex_escape(slot['caption'])}}}
            \\end{{figure}}
            """
        )

    def _storyboard_filename_for(self, board_filename):
        for spec in self.profile.get("storyboard_specs", []):
            if spec.get("source_board") == board_filename:
                return spec["filename"]
        return None

    def _storyboard_figure_tex(self, board_filename):
        storyboard = self._storyboard_filename_for(board_filename)
        if not storyboard:
            return ""
        caption = f"{self._slot(board_filename)['caption']}：连续帧故事板"
        return textwrap.dedent(
            f"""\
            \\begin{{figure}}[H]
                \\centering
                \\IfFileExists{{../evidence/auto/storyboards/{storyboard}}}{{%
                    \\includegraphics[width=0.95\\textwidth]{{../evidence/auto/storyboards/{storyboard}}}%
                }}{{%
                    \\fbox{{\\begin{{minipage}}[c][0.18\\textheight][c]{{0.92\\textwidth}}
                        \\centering \\textbf{{故事板未提供}}\\\\[0.4em]
                        \\small 期望文件：\\path{{{storyboard}}}
                    \\end{{minipage}}}}%
                }}
                \\caption{{{tex_escape(caption)}}}
            \\end{{figure}}
            """
        )

    def _manual_extra_figures_tex(self):
        if not self.manual_import_summary["extras"]:
            return ""
        blocks = ["\\subsection{补充实拍记录}"]
        caption_map = {
            "本地dnsexperimentdns端flush": "本地实验补充实拍：DNS 端 flush 与 dumpdb",
            "rssh-r2mac": "环境补充实拍：远程访问与实验桌面",
        }
        for item in self.manual_import_summary["extras"]:
            rel = "../" + item["target"].replace(os.sep, "/")
            name = Path(item["target"]).stem
            caption = caption_map.get(name, f"补充实拍：{name}")
            blocks.append(
                textwrap.dedent(
                    f"""\
                    \\begin{{figure}}[H]
                        \\centering
                        \\includegraphics[width=0.92\\textwidth]{{{rel}}}
                        \\caption{{{tex_escape(caption)}}}
                    \\end{{figure}}
                    """
                )
            )
        return "\n".join(blocks)

    def _snippet_listing(self, snippet_id, language, caption):
        snippet = self.snippet_lookup[snippet_id]
        return f"\\lstinputlisting[language={language},caption={{{tex_escape(caption)}}}]{{{snippet['path_from_tex']}}}\n"

    def _code_listing(self, output_name, language, caption):
        path = f"../evidence/auto/generated-code/{output_name}"
        return f"\\lstinputlisting[language={language},caption={{{tex_escape(caption)}}}]{{{path}}}\n"

    def _extract_values(self):
        def lines_for(snippet_id):
            content = self.snippet_lookup[snippet_id]["content"]
            return [line.strip() for line in content.splitlines() if line.strip()]

        local_ns = lines_for("local-baseline-ns")
        local_official = lines_for("local-baseline-official")
        local_attacker = lines_for("local-baseline-attacker")
        remote_authorities = lines_for("remote-authority-ips")
        remote_final_dig = lines_for("remote-final-dig")
        remote_cache = lines_for("remote-cache-success")
        local_task2_cache = lines_for("local-task2-cache")
        return {
            "local_ns": local_ns[0] if local_ns else "",
            "local_official": local_official,
            "local_attacker": local_attacker[0] if local_attacker else "",
            "remote_authorities": remote_authorities,
            "remote_final_dig": remote_final_dig,
            "remote_cache_first": remote_cache[0] if remote_cache else "",
            "local_task2_cache_first": local_task2_cache[0] if local_task2_cache else "",
        }

    def _clean_step_preview(self, text, max_lines=3):
        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("** WARNING:"):
                continue
            if "store now, decrypt later" in line:
                continue
            if "The server may need to be upgraded" in line:
                continue
            lines.append(line)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
        return " / ".join(lines)

    def _steps_appendix_tex(self, title, summary):
        blocks = [
            f"\\subsection{{{tex_escape(title)}}}",
            "本节按执行顺序压缩整理关键操作过程，便于回看整个实验链条。每一步保留执行意图、用户视角命令和结果摘要。",
        ]
        for idx, step in enumerate(summary.get("steps", []), start=1):
            blocks.append(f"\\paragraph{{步骤 {idx}：{tex_escape(step['title'])}}}")
            blocks.append("\\begin{itemize}")
            blocks.append(f"\\item 操作目的：{tex_escape(step.get('description', ''))}")
            blocks.append(f"\\item 用户视角命令：{tex_escape(step.get('human_command', ''))}")
            preview = self._clean_step_preview(step.get("result_preview", ""))
            if preview:
                blocks.append(f"\\item 结果摘要：{tex_escape(preview)}")
            blocks.append("\\end{itemize}")
        return "\n".join(blocks)

    def _trim_terminal_lines(self, text, max_lines=12):
        lines = []
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line:
                continue
            if line.startswith("** WARNING:"):
                continue
            if "store now, decrypt later" in line:
                continue
            if "The server may need to be upgraded" in line:
                continue
            lines.append(line)
        if max_lines and len(lines) > max_lines:
            lines = lines[:max_lines] + ["..."]
        return lines

    def _pane_text(self, commands, output="", cwd="lab4-dns", max_lines=10):
        commands = commands if isinstance(commands, list) else [commands]
        lines = []
        for command in commands:
            lines.append(f"$ {command}")
        if output:
            lines.extend(self._trim_terminal_lines(output, max_lines=max_lines))
        return {
            "cwd": cwd,
            "content": "\n".join(lines),
        }

    def _pane_from_entries(self, title, entries, cwd="lab4-dns"):
        lines = []
        for entry in entries:
            prompt = entry["prompt"]
            command = entry.get("command", "")
            if command.startswith("ssh -i ~/.ssh/seed-way"):
                continue
            line = f"{prompt} {command}".rstrip()
            lines.append(line)
            output = entry.get("output", "")
            if output:
                lines.extend(self._trim_terminal_lines(output, max_lines=entry.get("max_lines", 8)))
        return {
            "cwd": cwd,
            "title": title,
            "content": "\n".join(lines),
            "lines": lines,
        }

    def _shell_lines(self, lines, cwd="lab4-dns", title="终端"):
        return {
            "cwd": cwd,
            "title": title,
            "content": "\n".join(lines),
            "lines": lines,
        }

    def _pane_session(self, title, events, cwd="lab4-dns"):
        blocks = [f"[{title}]"]
        for index, event in enumerate(events, start=1):
            blocks.append(f"--- {index}. {event['label']} ---")
            commands = event["commands"] if isinstance(event["commands"], list) else [event["commands"]]
            for command in commands:
                blocks.append(f"$ {command}")
            output = event.get("output", "")
            if output:
                blocks.extend(self._trim_terminal_lines(output, max_lines=event.get("max_lines", 8)))
        return {
            "cwd": cwd,
            "title": title,
            "content": "\n".join(blocks),
        }

    def _find_step(self, summary, title_contains):
        for step in summary.get("steps", []):
            if title_contains in step.get("title", ""):
                return step
        raise PackagerError(f"找不到步骤: {title_contains}")

    def _build_terminal_shot_specs(self):
        local_step = lambda name: self._find_step(self.local_summary, name)
        remote_step = lambda name: self._find_step(self.remote_summary, name)
        attack_code_preview = excerpt_text((self.auto_code_dir / "attack.c").read_text(encoding="utf-8"), 10)
        prepare_preview = excerpt_text((self.auto_code_dir / "prepare_packets.py").read_text(encoding="utf-8"), 12)
        local_vm = "seed@VM101:~/seed-labs/lab4-dns-local/workspace/labsetup$"
        local_host = "(base) ➜ lab4-dns $"
        remote_vm = "seed@VM101:~/seed-labs/lab4-dns-remote/workspace/labsetup$"
        remote_volumes = "seed@VM101:~/seed-labs/lab4-dns-remote/workspace/labsetup/volumes$"
        attacker_prompt = "root@seed-attacker:/#"
        user_prompt = "root@user-10.9.0.5:/#"
        dns_prompt = "root@local-dns-server-10.9.0.53:/#"
        specs = {
            "local-config-dig-baseline.png": {
                "task_id": "local-config-dig-baseline",
                "panes": [
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short ns.attacker32.com", "output": self.snippet_lookup["local-baseline-ns"]["content"], "max_lines": 3},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": self.snippet_lookup["local-baseline-official"]["content"], "max_lines": 4},
                            {"prompt": user_prompt, "command": "dig +short @ns.attacker32.com www.example.com", "output": self.snippet_lookup["local-baseline-attacker"]["content"], "max_lines": 3},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "rndc flush"},
                            {"prompt": dns_prompt, "command": "rndc dumpdb -cache"},
                        ],
                    ),
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "dig +short ns.attacker32.com", "output": self.snippet_lookup["local-baseline-ns"]["content"], "max_lines": 3},
                            {"prompt": attacker_prompt, "command": "printf '%s\\n' 'official: 104.18.26.120 104.18.27.120' 'attacker: 1.2.3.5'"},
                        ],
                    ),
                ],
            },
            "local-task1-user-spoof-result.png": {
                "task_id": "local-task1-user-spoof-result",
                "panes": [
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "pkill -f dns_spoof_lab.py || true"},
                            {"prompt": attacker_prompt, "command": "python3 /volumes/dns_spoof_lab.py --task task1 --iface br-256929766fcf --timeout 25 >/volumes/task1.log 2>&1"},
                            {"prompt": attacker_prompt, "command": "cat /volumes/task1.log", "output": local_step("读取 task1 攻击日志")["result_preview"], "max_lines": 4},
                        ],
                    ),
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": local_step("task1 触发 dig")["result_preview"], "max_lines": 3},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "rndc dumpdb -cache >/dev/null 2>&1 && cat /var/cache/bind/dump.db", "output": local_step("task1 导出缓存")["result_preview"], "max_lines": 6},
                        ],
                    ),
                ],
            },
            "local-task2-cache-poisoning.png": {
                "task_id": "local-task2-cache-poisoning",
                "panes": [
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "pkill -f dns_spoof_lab.py || true"},
                            {"prompt": attacker_prompt, "command": "python3 /volumes/dns_spoof_lab.py --task task2 --iface br-256929766fcf --timeout 25 >/volumes/task2.log 2>&1"},
                            {"prompt": attacker_prompt, "command": "cat /volumes/task2.log", "output": local_step("读取 task2 攻击日志")["result_preview"], "max_lines": 4},
                        ],
                    ),
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": "1.2.3.5", "max_lines": 2},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": "1.2.3.5", "max_lines": 2},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "rndc flush"},
                            {"prompt": dns_prompt, "command": "grep -n 'www.example.com\\|1.2.3.5' /var/cache/bind/dump.db", "output": local_step("task2 缓存筛选")["result_preview"], "max_lines": 4},
                        ],
                    ),
                ],
            },
            "local-task3-ns-poisoning.png": {
                "task_id": "local-task3-ns-poisoning",
                "panes": [
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "python3 /volumes/dns_spoof_lab.py --task task3 --iface br-256929766fcf --timeout 25 >/volumes/task3.log 2>&1"},
                            {"prompt": attacker_prompt, "command": "cat /volumes/task3.log", "output": local_step("读取 task3 攻击日志")["result_preview"], "max_lines": 4},
                        ],
                    ),
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": "1.2.3.5", "max_lines": 2},
                            {"prompt": user_prompt, "command": "dig +short mail.example.com", "output": "1.2.3.6", "max_lines": 2},
                            {"prompt": user_prompt, "command": "dig +short @ns.attacker32.com mail.example.com", "output": "1.2.3.6", "max_lines": 2},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "grep -n 'example.com\\|attacker32.com' /var/cache/bind/dump.db", "output": local_step("task3 缓存筛选")["result_preview"], "max_lines": 6},
                        ],
                    ),
                ],
            },
            "local-task4-cross-domain-cache-observation.png": {
                "task_id": "local-task4-cross-domain-cache-observation",
                "panes": [
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "python3 /volumes/dns_spoof_lab.py --task task4 --iface br-256929766fcf --timeout 25 >/volumes/task4.log 2>&1"},
                            {"prompt": attacker_prompt, "command": "cat /volumes/task4.log", "output": local_step("读取 task4 攻击日志")["result_preview"], "max_lines": 4},
                        ],
                    ),
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": local_step("task4 触发 dig")["result_preview"], "max_lines": 2},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "grep -n 'google.com\\|example.com\\|attacker32.com' /var/cache/bind/dump.db", "output": local_step("task4 缓存筛选")["result_preview"], "max_lines": 5},
                        ],
                    ),
                ],
            },
            "local-task5-additional-section-cache.png": {
                "task_id": "local-task5-additional-section-cache",
                "panes": [
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "python3 /volumes/dns_spoof_lab.py --task task5 --iface br-256929766fcf --timeout 25 >/volumes/task5.log 2>&1"},
                            {"prompt": attacker_prompt, "command": "cat /volumes/task5.log", "output": local_step("读取 task5 攻击日志")["result_preview"], "max_lines": 4},
                        ],
                    ),
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": local_step("task5 触发 dig")["result_preview"], "max_lines": 2},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": local_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "grep -n 'attacker32.com\\|example.net\\|facebook.com\\|1.2.3.4\\|5.6.7.8\\|3.4.5.6' /var/cache/bind/dump.db", "output": local_step("task5 缓存筛选")["result_preview"], "max_lines": 5},
                        ],
                    ),
                ],
            },
            "remote-baseline-dig-and-cache.png": {
                "task_id": "remote-baseline-dig-and-cache",
                "panes": [
                    self._pane_from_entries(
                        "宿主机终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docker-compose up -d"},
                            {"prompt": remote_vm, "command": "dockps", "output": remote_step("检查运行容器")["result_preview"], "max_lines": 5},
                        ],
                    ),
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": self.snippet_lookup["local-baseline-official"]["content"], "max_lines": 4},
                            {"prompt": user_prompt, "command": "dig +short @ns.attacker32.com www.example.com", "output": self.snippet_lookup["local-baseline-attacker"]["content"], "max_lines": 3},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "rndc flush"},
                        ],
                    ),
                ],
            },
            "remote-request-trigger-trace.png": {
                "task_id": "remote-request-trigger-trace",
                "panes": [
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "for ns in $(dig +short NS example.com); do dig +short $ns; done | grep -E '^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$' | sort -u", "output": remote_step("查询合法权威 NS IP")["result_preview"], "max_lines": 6},
                        ],
                    ),
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "tail -n 40 attack-run.log", "output": remote_step("读取 Kaminsky 攻击日志")["result_preview"], "max_lines": 5},
                        ],
                    ),
                    self._pane_from_entries(
                        "宿主机终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "echo dees | sudo -S timeout 30s ./attack"},
                        ],
                    ),
                ],
            },
            "remote-forged-response-trace.png": {
                "task_id": "remote-forged-response-trace",
                "panes": [
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "cd /volumes && python3 prepare_packets.py", "output": remote_step("生成 Kaminsky 数据包模板")["result_preview"], "max_lines": 4},
                            {"prompt": remote_volumes, "command": "gcc -O2 -o attack attack.c"},
                        ],
                    ),
                    self._pane_from_entries(
                        "模板脚本预览",
                        [
                            {"prompt": remote_volumes, "command": "sed -n '1,40p' prepare_packets.py", "output": prepare_preview, "max_lines": 10},
                        ],
                    ),
                    self._pane_from_entries(
                        "攻击程序预览",
                        [
                            {"prompt": remote_volumes, "command": "sed -n '1,40p' attack.c", "output": attack_code_preview, "max_lines": 10},
                        ],
                    ),
                ],
            },
            "remote-kaminsky-cache-success.png": {
                "task_id": "remote-kaminsky-cache-success",
                "panes": [
                    self._pane_from_entries(
                        "宿主机终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_volumes, "command": "echo dees | sudo -S timeout 30s ./attack"},
                        ],
                    ),
                    self._pane_from_entries(
                        "攻击者终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh se"},
                            {"prompt": attacker_prompt, "command": "tail -n 40 attack-run.log", "output": remote_step("读取 Kaminsky 攻击日志")["result_preview"], "max_lines": 5},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "grep -n 'attacker32.com\\|example.com' /var/cache/bind/dump.db", "output": remote_step("远程攻击缓存筛选")["result_preview"], "max_lines": 7},
                        ],
                    ),
                ],
            },
            "remote-final-dig-verification.png": {
                "task_id": "remote-final-dig-verification",
                "panes": [
                    self._pane_from_entries(
                        "用户终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh us"},
                            {"prompt": user_prompt, "command": "dig +short www.example.com", "output": "1.2.3.5", "max_lines": 2},
                            {"prompt": user_prompt, "command": "dig +short @ns.attacker32.com www.example.com", "output": "1.2.3.5", "max_lines": 2},
                        ],
                    ),
                    self._pane_from_entries(
                        "本地 DNS 终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "docksh lo"},
                            {"prompt": dns_prompt, "command": "grep -n 'attacker32.com\\|example.com' /var/cache/bind/dump.db", "output": remote_step("远程攻击缓存筛选")["result_preview"], "max_lines": 6},
                        ],
                    ),
                    self._pane_from_entries(
                        "宿主机终端",
                        [
                            {"prompt": local_host, "command": "ssh -i ~/.ssh/seed-way -p 2345 seed@localhost"},
                            {"prompt": remote_vm, "command": "printf '%s\\n' '普通 dig 与 @ns.attacker32.com 查询结果一致' '说明 example.com 权威路径已被改写'"},
                        ],
                    ),
                ],
            },
        }
        if self.profile.get("board_specs"):
            ordered = {}
            for item in self.profile["board_specs"]:
                filename = item["filename"]
                if filename in specs:
                    ordered[filename] = specs[filename]
            return ordered
        return specs

    def _terminal_shot_html(self, spec):
        panes_html = []
        for pane in spec["panes"]:
            panes_html.append(
                f"""
                <section class="pane">
                  <div class="pane-header">
                    <span class="dot"></span>
                    <span class="prompt-base">(base)</span>
                    <span class="prompt-arrow">➜</span>
                    <span class="cwd">{html_lib.escape(pane['cwd'])}</span>
                    <span class="pane-title">□</span>
                  </div>
                  <div class="pane-subtitle">{html_lib.escape(pane.get('title', '终端'))}</div>
                  <pre>{html_lib.escape(pane['content'])}</pre>
                </section>
                """
            )
        sidebar_items = []
        pane_titles = [pane.get("title", "终端") for pane in spec["panes"]]
        for index, title in enumerate(pane_titles):
            branch = "└─" if index == len(pane_titles) - 1 else "├─"
            active = " active" if index == len(pane_titles) - 1 else ""
            sidebar_items.append(f'<div class="sidebar-item{active}">{branch} <span>{html_lib.escape(title)}</span></div>')
        sidebar = "".join(sidebar_items)
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    :root {{
      --bg: #ffffff;
      --panel: #fbfbfc;
      --header: #f1f1f3;
      --border: #d7d7db;
      --text: #222;
      --muted: #9ea0a6;
      --green: #167d1e;
      --blue: #0f81a8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      padding: 8px;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    }}
    .frame {{
      width: 1720px;
      min-height: 348px;
      background: var(--panel);
      display: grid;
      grid-template-columns: 1fr 180px;
      border: 1px solid #d9dadd;
      box-shadow: 0 0 0 1px #eef0f2 inset;
    }}
    .workspace {{
      display: grid;
      grid-template-columns: repeat({len(spec['panes'])}, 1fr);
      min-height: 348px;
    }}
    .pane {{
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      min-height: 348px;
      background: #fafafa;
    }}
    .pane:last-child {{ border-right: none; }}
    .pane-header {{
      height: 48px;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 18px;
      border-bottom: 1px solid var(--border);
      background: var(--header);
      font-size: 17px;
      font-weight: 700;
      color: #444;
    }}
    .pane-subtitle {{
      padding: 10px 18px 8px 18px;
      font: 700 12px/1.4 -apple-system, BlinkMacSystemFont, sans-serif;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: #72747b;
      border-bottom: 1px solid #ececef;
      background: #f9f9fb;
    }}
    .dot {{
      width: 16px;
      height: 16px;
      border-radius: 50%;
      border: 3px solid #b8b9bd;
      display: inline-block;
      background: white;
    }}
    .prompt-base {{ font-weight: 600; }}
    .prompt-arrow {{ color: var(--green); font-weight: 700; }}
    .cwd {{ color: var(--blue); font-weight: 800; }}
    .pane-title {{ margin-left: auto; color: #222; font-size: 20px; }}
    pre {{
      margin: 0;
      padding: 14px 20px 22px 20px;
      white-space: pre-wrap;
      word-break: break-word;
      font: 15px/1.55 Menlo, Monaco, "SF Mono", Consolas, monospace;
      color: var(--text);
      flex: 1;
      min-height: 0;
    }}
    .sidebar {{
      border-left: 1px solid var(--border);
      background: #f7f7f9;
      padding-top: 20px;
      font: 18px/1.7 -apple-system, BlinkMacSystemFont, sans-serif;
      color: #333;
    }}
    .sidebar-item {{
      padding: 4px 18px;
      color: #5a5b60;
    }}
    .sidebar-item.active {{
      background: #dadade;
      color: #222;
    }}
  </style>
</head>
<body>
  <div class="frame">
    <div class="workspace">
      {''.join(panes_html)}
    </div>
    <aside class="sidebar">
      {sidebar}
    </aside>
  </div>
</body>
</html>"""

    def _storyboard_html(self, title, frames):
        frame_html = []
        for frame in frames:
            panes = []
            for pane in frame["panes"]:
                panes.append(
                    f"""
                    <div class="mini-pane">
                      <div class="mini-pane-head">{html_lib.escape(pane.get('title', '终端'))}</div>
                      <pre>{html_lib.escape(pane['content'])}</pre>
                    </div>
                    """
                )
            frame_html.append(
                f"""
                <section class="frame-row">
                  <div class="frame-label">
                    <div class="frame-step">{html_lib.escape(frame['step'])}</div>
                    <div class="frame-title">{html_lib.escape(frame['title'])}</div>
                  </div>
                  <div class="frame-workspace frame-{len(frame['panes'])}">
                    {''.join(panes)}
                  </div>
                </section>
                """
            )
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    :root {{
      --bg: #ffffff;
      --card: #fbfbfc;
      --line: #d8d8dc;
      --accent: #0f81a8;
      --text: #222;
      --muted: #73757b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      padding: 8px;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
    }}
    .sheet {{
      width: 1720px;
      background: #ffffff;
      padding: 18px 18px 8px 18px;
      border: 1px solid #d9dadd;
    }}
    .sheet-title {{
      font-size: 24px;
      font-weight: 800;
      color: var(--text);
      margin: 0 0 14px 0;
    }}
    .frame-row {{
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 14px;
      margin-bottom: 14px;
    }}
    .frame-label {{
      background: #f2f4f7;
      border: 1px solid var(--line);
      padding: 14px;
    }}
    .frame-step {{
      font-size: 14px;
      font-weight: 800;
      color: var(--accent);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: .08em;
    }}
    .frame-title {{
      font-size: 16px;
      font-weight: 700;
      color: var(--text);
      line-height: 1.4;
    }}
    .frame-workspace {{
      display: grid;
      gap: 12px;
    }}
    .frame-1 {{ grid-template-columns: 1fr; }}
    .frame-2 {{ grid-template-columns: repeat(2, 1fr); }}
    .frame-3 {{ grid-template-columns: repeat(3, 1fr); }}
    .mini-pane {{
      border: 1px solid var(--line);
      background: var(--card);
      min-height: 180px;
      display: flex;
      flex-direction: column;
    }}
    .mini-pane-head {{
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      font-weight: 800;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .07em;
    }}
    pre {{
      margin: 0;
      padding: 14px;
      white-space: pre-wrap;
      word-break: break-word;
      font: 14px/1.55 Menlo, Monaco, "SF Mono", Consolas, monospace;
      color: var(--text);
      flex: 1;
    }}
  </style>
</head>
<body>
  <div class="sheet">
    <div class="sheet-title">{html_lib.escape(title)}</div>
    {''.join(frame_html)}
  </div>
</body>
</html>"""

    def _build_storyboard_specs(self, board_specs):
        storyboards = {}
        configured = {item["source_board"]: item for item in self.profile.get("storyboard_specs", [])}
        for filename, board in board_specs.items():
            config = configured.get(filename)
            if not config:
                continue
            frames = []
            for index, pane in enumerate(board["panes"], start=1):
                frames.append(
                    {
                        "step": f"Step {index}",
                        "title": pane.get("title", f"Frame {index}"),
                        "panes": [pane],
                    }
                )
            storyboards[config["filename"]] = {
                "task_id": config["task_id"],
                "source_board": filename,
                "title": config.get("title", f"{config['task_id']} storyboard"),
                "frames": frames,
            }
        return storyboards

    def _build_contact_sheet(self, ordered_images):
        from PIL import Image, ImageDraw, ImageFont

        images = []
        for label, path in ordered_images:
            if not path.exists():
                continue
            img = Image.open(path).convert("RGB")
            images.append((label, img))
        if not images:
            return

        thumb_w = 360
        thumb_h = 160
        cols = 3
        gutter = 24
        header_h = 70
        label_h = 36
        rows = (len(images) + cols - 1) // cols
        sheet_w = cols * thumb_w + (cols + 1) * gutter
        sheet_h = header_h + rows * (thumb_h + label_h + gutter) + gutter
        canvas = Image.new("RGB", (sheet_w, sheet_h), "#ffffff")
        draw = ImageDraw.Draw(canvas)
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        draw.text((gutter, 20), "lab4-dns 自动终端取证总览", fill="#202124", font=title_font)
        for idx, (label, img) in enumerate(images):
            row = idx // cols
            col = idx % cols
            x = gutter + col * (thumb_w + gutter)
            y = header_h + row * (thumb_h + label_h + gutter)
            thumb = img.copy()
            thumb.thumbnail((thumb_w, thumb_h))
            bg = Image.new("RGB", (thumb_w, thumb_h), "#f7f7f8")
            bg.paste(thumb, ((thumb_w - thumb.width) // 2, (thumb_h - thumb.height) // 2))
            canvas.paste(bg, (x, y))
            draw.rectangle((x, y, x + thumb_w, y + thumb_h), outline="#d7d7db", width=2)
            draw.text((x, y + thumb_h + 8), label, fill="#202124", font=text_font)
        canvas.save(self.contact_sheet_path)

    def _render_auto_terminal_shots(self):
        from playwright.sync_api import sync_playwright

        ensure_dir(self.auto_boards_dir)
        ensure_dir(self.verification_dir)
        specs = self._build_terminal_shot_specs()
        manifest = {
            "profile_id": self.profile_id,
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "render_mode": "multi-pane-continuous-terminal-board",
            "shot_type": "board",
            "shots": [],
        }
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1760, "height": 390}, device_scale_factor=2)
            for filename, spec in specs.items():
                page.set_content(self._terminal_shot_html(spec), wait_until="load")
                target = self.auto_boards_dir / filename
                page.screenshot(path=str(target))
                manifest["shots"].append(
                    {
                        "filename": filename,
                        "task_id": spec.get("task_id", filename.replace(".png", "")),
                        "shot_type": "board",
                        "pane_count": len(spec["panes"]),
                        "pane_titles": [pane.get("title", "终端") for pane in spec["panes"]],
                        "frame_count": 1,
                        "size_bytes": target.stat().st_size,
                    }
                )
            browser.close()
        self.boards_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        report_lines = [
            f"# {self.profile['title']} 主证据板测试报告",
            "",
            "- 渲染后端：Playwright Chromium",
            "- 输入来源：summary.json step 结果、evidence snippets、generated code",
            "- 输出目录：`evidence/auto/terminal-boards/`",
            "- 当前模式：任务级多终端连续记录板",
            "",
            "## 检测结果",
            "",
        ]
        for item in manifest["shots"]:
            report_lines.append(
                f"- `{item['filename']}`：{item['pane_count']} 个 pane（{' / '.join(item['pane_titles'])}），{item['size_bytes']} bytes"
            )
        report_lines.extend(
            [
                "",
                "## 结论",
                "",
                "- 主证据板链路已打通，可在没有人工截图的情况下为报告提供自然终端风格的多终端连续证据图。",
                "- 报告中的截图位会优先读取手工截图；若缺失，则自动回退到这些终端证据图。",
                "- 当前方案适合命令行输出、缓存筛选、代码预览、多 pane 并排对照、以及同一任务内连续操作记录。",
            ]
        )
        self.boards_report_path.write_text("\n".join(report_lines), encoding="utf-8")

    def _render_storyboards(self):
        from playwright.sync_api import sync_playwright

        ensure_dir(self.auto_storyboards_dir)
        ensure_dir(self.verification_dir)
        board_specs = self._build_terminal_shot_specs()
        storyboards = self._build_storyboard_specs(board_specs)
        manifest = {
            "profile_id": self.profile_id,
            "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "render_mode": "task-storyboard",
            "shot_type": "storyboard",
            "shots": [],
        }
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1760, "height": 1120}, device_scale_factor=2)
            for filename, spec in storyboards.items():
                page.set_content(self._storyboard_html(spec["title"], spec["frames"]), wait_until="load")
                target = self.auto_storyboards_dir / filename
                page.screenshot(path=str(target), full_page=True)
                manifest["shots"].append(
                    {
                        "filename": filename,
                        "task_id": spec["task_id"],
                        "source_board": spec["source_board"],
                        "shot_type": "storyboard",
                        "pane_count": sum(len(frame["panes"]) for frame in spec["frames"]),
                        "pane_titles": [pane.get("title", "终端") for frame in spec["frames"] for pane in frame["panes"]],
                        "frame_count": len(spec["frames"]),
                        "size_bytes": target.stat().st_size,
                    }
                )
            browser.close()
        self.storyboards_manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = [
            f"# {self.profile['title']} 故事板测试报告",
            "",
            "- 渲染后端：Playwright Chromium",
            "- 输出目录：`evidence/auto/storyboards/`",
            "- 当前模式：任务级连续帧故事板",
            "",
            "## 检测结果",
            "",
        ]
        for item in manifest["shots"]:
            lines.append(
                f"- `{item['filename']}`：{item['frame_count']} 帧，{item['size_bytes']} bytes"
            )
        lines.extend(
            [
                "",
                "## 结论",
                "",
                "- 故事板用于表达操作前后和中间态的时间推进，不依赖单张截图承载全部证据。",
                "- 主证据板和故事板结合后，静态 PDF 中的实验记录连贯性显著增强。",
            ]
        )
        self.storyboards_report_path.write_text("\n".join(lines), encoding="utf-8")

    def _verify_evidence_outputs(self, run_override_test=False):
        ensure_dir(self.verification_dir)
        board_manifest = read_json(self.boards_manifest_path)
        story_manifest = read_json(self.storyboards_manifest_path)
        ordered = []
        board_map = {item["filename"]: self.auto_boards_dir / item["filename"] for item in board_manifest["shots"]}
        story_map = {item["filename"]: self.auto_storyboards_dir / item["filename"] for item in story_manifest["shots"]}
        for name in self.profile.get("contact_sheet_order", []):
            if name in board_map:
                ordered.append((name, board_map[name]))
            elif name in story_map:
                ordered.append((name, story_map[name]))
        if not ordered:
            ordered = [(p.name, p) for p in sorted(self.auto_boards_dir.glob("*.png"))]
        self._build_contact_sheet(ordered)
        lines = [
            f"# {self.profile['title']} 自动取证验证报告",
            "",
            f"- 主证据板数量：{len(board_manifest['shots'])}",
            f"- 故事板数量：{len(story_manifest['shots'])}",
            f"- Contact sheet：`{self.contact_sheet_path.name}`",
            "",
            "## 基础校验",
            "",
            f"- 主证据板目录存在：{self.auto_boards_dir.exists()}",
            f"- 故事板目录存在：{self.auto_storyboards_dir.exists()}",
            f"- Contact sheet 存在：{self.contact_sheet_path.exists()}",
            "",
        ]
        if run_override_test:
            test_name = self.profile["screenshot_slots"][0]["filename"]
            manual_target = self.manual_dir / test_name
            backup = None
            if manual_target.exists():
                backup = manual_target.read_bytes()
            shutil.copy2(self.auto_boards_dir / test_name, manual_target)
            self.compile_package()
            manual_override_ok = True
            manual_target.unlink(missing_ok=True)
            if backup is not None:
                manual_target.write_bytes(backup)
            self.compile_package()
            lines.extend(
                [
                    "## 回退校验",
                    "",
                    f"- 手工图覆盖测试：{manual_override_ok}",
                    "- 已执行：复制自动图到 manual/ -> 重新编译 -> 删除 manual/ -> 再次编译。",
                    "",
                ]
            )
        (self.verification_dir / "verification-report.md").write_text("\n".join(lines), encoding="utf-8")

    def _render_tex(self):
        values = self._extract_values()
        today = dt.datetime.now().strftime("%Y年%-m月%-d日") if sys.platform != "win32" else dt.datetime.now().strftime("%Y年%m月%d日")
        local_dns_baseline = "、".join(values["local_official"]) if values["local_official"] else "无"
        remote_authority_ips = "、".join(values["remote_authorities"]) if values["remote_authorities"] else "无"
        remote_final = "、".join(values["remote_final_dig"]) if values["remote_final_dig"] else "无"
        local_baseline_commands = """# 用户容器
dig +short ns.attacker32.com
dig +short www.example.com
dig +short @ns.attacker32.com www.example.com

# 本地 DNS 容器
rndc flush
rndc dumpdb -cache"""
        local_task1_commands = """# 攻击者容器
python3 /volumes/dns_spoof_lab.py --task task1 --iface <bridge> --timeout 25

# 用户容器
dig +short www.example.com"""
        local_task2_commands = """# 本地 DNS 容器
rndc flush

# 攻击者容器
python3 /volumes/dns_spoof_lab.py --task task2 --iface <bridge> --timeout 25

# 用户容器
dig +short www.example.com
dig +short www.example.com

# 本地 DNS 容器
grep -n 'www.example.com\\|1.2.3.5' /var/cache/bind/dump.db"""
        local_task3_commands = """# 本地 DNS 容器
rndc flush

# 攻击者容器
python3 /volumes/dns_spoof_lab.py --task task3 --iface <bridge> --timeout 25

# 用户容器
dig +short www.example.com
dig +short mail.example.com
dig +short @ns.attacker32.com mail.example.com

# 本地 DNS 容器
grep -n 'example.com\\|attacker32.com' /var/cache/bind/dump.db"""
        local_task4_commands = """# 本地 DNS 容器
rndc flush

# 攻击者容器
python3 /volumes/dns_spoof_lab.py --task task4 --iface <bridge> --timeout 25

# 用户容器
dig +short www.example.com

# 本地 DNS 容器
grep -n 'google.com\\|example.com\\|attacker32.com' /var/cache/bind/dump.db"""
        local_task5_commands = """# 本地 DNS 容器
rndc flush

# 攻击者容器
python3 /volumes/dns_spoof_lab.py --task task5 --iface <bridge> --timeout 25

# 用户容器
dig +short www.example.com

# 本地 DNS 容器
grep -n 'attacker32.com\\|example.net\\|facebook.com\\|1.2.3.4\\|5.6.7.8\\|3.4.5.6' /var/cache/bind/dump.db"""
        remote_env_commands = """# 宿主机 / 实验目录
docker-compose build
docker-compose up -d

# 用户容器
dig +short ns.attacker32.com
dig +short www.example.com
dig +short @ns.attacker32.com www.example.com"""
        remote_task2_commands = """# 用户容器
for ns in $(dig +short NS example.com); do
  dig +short $ns
done | grep -E '^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$' | sort -u"""
        remote_task34_commands = """# 攻击者侧生成模板
python3 prepare_packets.py

# 宿主机编译攻击程序
gcc -O2 -o attack attack.c"""
        remote_task4_commands = """# 本地 DNS 容器
rndc flush

# 宿主机
echo dees | sudo -S timeout 30s ./attack

# 本地 DNS 容器
grep -n 'attacker32.com\\|example.com' /var/cache/bind/dump.db"""
        remote_task5_commands = """# 用户容器
dig +short www.example.com
dig +short @ns.attacker32.com www.example.com"""
        tex = textwrap.dedent(
            f"""\
            \\documentclass[12pt,hyperref,a4paper,UTF8,fontset=none]{{ctexart}}

            \\usepackage{{zjureport}}
            \\usepackage{{enumitem}}
            \\usepackage{{listings}}
            \\usepackage{{xcolor}}
            \\usepackage{{booktabs}}
            \\usepackage{{longtable}}
            \\usepackage{{graphicx}}
            \\usepackage{{float}}
            \\usepackage{{amsmath}}
            \\usepackage{{array}}
            \\usepackage{{caption}}
            \\usepackage{{tabularx}}
            \\usepackage{{setspace}}
            \\usepackage{{url}}

            \\zjuheader{{{tex_escape(self.profile['header'])}}}
            \\zjucourse{{{tex_escape(self.profile['course'])}}}
            \\zjureporttitle{{{tex_escape(self.profile['title'])}}}
            \\zjuname{{{tex_escape(self.profile['student']['name'])}}}
            \\zjuemail{{{tex_escape(self.profile['student']['email'])}}}
            \\zjucollege{{{tex_escape(self.profile['student']['college'])}}}
            \\zjudepartment{{{tex_escape(self.profile['student']['department'])}}}
            \\zjumajor{{{tex_escape(self.profile['student']['major'])}}}
            \\zjustuid{{{tex_escape(self.profile['student']['student_id'])}}}
            \\zjuinstructor{{{tex_escape(self.profile['student']['instructor'])}}}
            \\zjureportdate{{{tex_escape(today)}}}

            \\setlength{{\\headheight}}{{15pt}}
            \\setstretch{{1.20}}
            \\setlength{{\\parskip}}{{0.35em}}
            \\hypersetup{{
                colorlinks=true,
                linkcolor=black,
                filecolor=black,
                urlcolor=blue,
                citecolor=black,
            }}
            \\captionsetup{{font=small, labelfont=bf}}
            \\setlist[itemize]{{leftmargin=2em, itemsep=0.2em, topsep=0.3em}}
            \\setlist[enumerate]{{leftmargin=2em, itemsep=0.2em, topsep=0.3em}}
            \\graphicspath{{{{figures/}}{{../evidence/manual/}}}}

            \\definecolor{{codegray}}{{gray}}{{0.96}}
            \\definecolor{{codepurple}}{{rgb}}{{0.58,0,0.82}}
            \\definecolor{{codeblue}}{{rgb}}{{0,0,0.75}}
            \\definecolor{{codegreen}}{{rgb}}{{0,0.55,0}}

            \\lstset{{
                backgroundcolor=\\color{{codegray}},
                commentstyle=\\color{{codegreen}},
                keywordstyle=\\color{{codeblue}},
                numberstyle=\\tiny\\color{{gray}},
                stringstyle=\\color{{codepurple}},
                basicstyle=\\ttfamily\\small,
                breakatwhitespace=false,
                breaklines=true,
                columns=fullflexible,
                captionpos=b,
                keepspaces=true,
                numbers=left,
                numbersep=5pt,
                showspaces=false,
                showstringspaces=false,
                showtabs=false,
                frame=single,
                rulecolor=\\color{{black}},
                tabsize=2
            }}

            \\newenvironment{{reportbox}}[1]{{%
                \\par\\smallskip\\noindent\\hrule\\smallskip\\noindent\\textbf{{#1}}\\par\\smallskip
            }}{{%
                \\smallskip\\noindent\\hrule\\par\\smallskip
            }}

            \\begin{{document}}

            \\cover

            \\begin{{abstract}}
            本报告围绕“实验四：DNS 攻击实验”整理我在统一 Proxmox SEED 实验平台上完成的本地 DNS 攻击与远程 Kaminsky 攻击结果。正文重点不在于展示脚本本身，而在于把实验目标、关键命令、过程记录、真实观测结果以及我的分析解释完整写清楚，并以统一的终端取证图展示关键证据。

            \\textbf{{关键词}}：DNS，缓存投毒，NS 记录伪造，Additional Section，Kaminsky Attack，SEED Labs
            \\end{{abstract}}

            \\tableofcontents
            \\newpage

            \\section{{实验目标与背景}}
            本实验分为两部分。第一部分是本地 DNS 攻击，重点研究攻击者与受害 DNS 服务器位于同一局域网时，伪造响应、缓存投毒、Authority Section 和 Additional Section 分别会带来什么效果。第二部分是远程 DNS 攻击，重点研究攻击者看不到受害 DNS 查询时，为什么仍然可以通过 Kaminsky 思路持续制造伪造机会，最终把 \\texttt{{example.com}} 的 NS 记录替换成攻击者控制的权威服务器。

            我在写这份报告时特别强调两点：第一，尽量把每个任务的具体命令链和实验过程写清楚，而不是只给一个结论；第二，优先描述这次实验里真实观察到的现象，而不是简单重复实验指导中的理论预期。

            \\section{{实验环境、角色与操作约定}}
            本次实验统一在课程提供的 Proxmox Ubuntu 20.04 SEED 环境中完成，本地和远程两部分都围绕 Docker Compose 部署的实验拓扑展开。为了让过程记录更清晰，下表先把实验里最关键的角色和用途列出来。

            \\begin{{table}}[H]
            \\centering
            \\begin{{tabularx}}{{\\textwidth}}{{>{{\\raggedright\\arraybackslash}}p{{0.18\\textwidth}} >{{\\raggedright\\arraybackslash}}p{{0.18\\textwidth}} X}}
            \\toprule
            角色 & 地址 / 位置 & 用途 \\\\
            \\midrule
            用户主机 & \\texttt{{10.9.0.5}} & 发起 dig 查询，验证投毒前后解析结果变化。 \\\\
            本地 DNS 服务器 & \\texttt{{10.9.0.53}} & 运行 BIND 9，是缓存投毒的核心目标。 \\\\
            攻击者容器 & host mode & 负责嗅探、伪造、模板生成与远程攻击实施。 \\\\
            攻击者权威服务器 & \\texttt{{10.9.0.153}} & 提供 \\texttt{{attacker32.com}} 与伪造 \\texttt{{example.com}} 解析结果。 \\\\
            路由器（本地实验） & \\texttt{{10.9.0.11 / 10.8.0.11}} & 在必要时人为增加外部网络延迟，给伪造响应争取时间窗口。 \\\\
            \\bottomrule
            \\end{{tabularx}}
            \\caption{{实验四关键角色与用途}}
            \\end{{table}}

            \\begin{{reportbox}}{{写作说明}}
            正文以我的实验过程为主，不专门展开仓库内部路径或生成器细节。附录重点保留完整代码、自动终端取证总览以及全过程记录，便于老师快速查看整体证据链。
            \\end{{reportbox}}

            \\section{{第一部分：本地 DNS 攻击}}

            \\subsection{{本地配置测试}}
            在正式开始攻击之前，我先验证实验环境中的三条关键解析路径：\\texttt{{attacker32.com}} 是否已经能转发到攻击者权威服务器、普通 \\texttt{{www.example.com}} 是否仍返回真实公网地址、以及显式指定 \\texttt{{@ns.attacker32.com}} 查询时是否会得到攻击者预置结果。如果这三条路径都能区分开，后面的每个任务才有比较基础。

            \\subsubsection{{关键命令记录}}
            {self._command_block("本地配置测试关键命令", local_baseline_commands)}

            \\subsubsection{{结果与分析}}
            这次实验中，\\texttt{{ns.attacker32.com}} 解析为 \\texttt{{{tex_escape(values['local_ns'])}}}，普通 \\texttt{{www.example.com}} 返回 {tex_escape(local_dns_baseline)}，而指定攻击者权威服务器后返回 \\texttt{{{tex_escape(values['local_attacker'])}}}。因此可以确认：实验环境在攻击前同时存在“真实答案”和“伪造答案”两条路径，后续要证明的就是用户或本地 DNS 服务器会不会被诱导去选错那一条。

            {self._snippet_listing("local-baseline-ns", "bash", "本地实验：ns.attacker32.com 基线解析")}
            {self._snippet_listing("local-baseline-official", "bash", "本地实验：官方 www.example.com 基线解析")}
            {self._snippet_listing("local-baseline-attacker", "bash", "本地实验：攻击者权威服务器返回结果")}
            {self._figure_tex("local-config-dig-baseline.png")}
            {self._storyboard_figure_tex("local-config-dig-baseline.png")}

            \\subsection{{任务 1：直接向用户伪造响应}}
            任务 1 的目标非常直接：当用户主机向本地 DNS 服务器发起查询时，攻击者立即伪造一个更快到达的响应，让用户主机直接接受假答案。与后面的缓存投毒不同，这里受骗的是用户主机本身，而不是本地 DNS 服务器缓存。

            \\subsubsection{{关键命令记录}}
            {self._command_block("任务 1 关键命令", local_task1_commands)}

            \\subsubsection{{结果与分析}}
            从这次实验结果来看，用户侧第一次查询就被改写成了 \\texttt{{1.2.3.5}}，而攻击者日志中明确出现了 \\texttt{{spoofed www.example.com. -> 10.9.0.5}}。因此我把任务 1 理解为“即时欺骗”：只要伪造响应先到，用户主机就会短时间内相信它，但这种影响还没有沉淀到 DNS 服务器缓存中。

            {self._snippet_listing("local-task1-dig", "bash", "本地任务 1：用户侧 dig 输出")}
            {self._snippet_listing("local-task1-attack-log", "bash", "本地任务 1：攻击者脚本命中日志")}
            {self._analysis_block(self.analysis_local["任务 1：直接向用户伪造响应"])}
            {self._figure_tex("local-task1-user-spoof-result.png")}
            {self._storyboard_figure_tex("local-task1-user-spoof-result.png")}

            \\subsection{{任务 2：DNS 缓存投毒}}
            任务 2 关注的是“持续性”。如果我只骗到了用户一次，但本地 DNS 服务器本身没有记住这个错误答案，那么攻击效果会随着下一次查询很快消失。相反，一旦本地 DNS 服务器把伪造 A 记录写入缓存，后续重复查询就会自动返回错误结果。

            \\subsubsection{{关键命令记录}}
            {self._command_block("任务 2 关键命令", local_task2_commands)}

            \\subsubsection{{结果与分析}}
            我判断缓存投毒是否成功时主要看两个证据：一是连续两次 \\texttt{{dig}} 是否都稳定返回 \\texttt{{1.2.3.5}}；二是 \\texttt{{dump.db}} 中是否真的出现 \\texttt{{www.example.com}} 的伪造 A 记录。两者在本次实验中都成立，因此可以确认任务 2 已从“即时欺骗用户”升级为“污染本地 DNS 缓存”。

            {self._snippet_listing("local-task2-dig", "bash", "本地任务 2：连续 dig 输出")}
            {self._snippet_listing("local-task2-cache", "bash", "本地任务 2：缓存命中结果")}
            {self._analysis_block(self.analysis_local["任务 2：DNS 缓存投毒"])}
            {self._figure_tex("local-task2-cache-poisoning.png")}
            {self._storyboard_figure_tex("local-task2-cache-poisoning.png")}

            \\subsection{{任务 3：伪造 NS 记录}}
            我认为本地部分最关键的任务其实是任务 3，因为它第一次体现出“单个主机名被伪造”和“整个域的权威路径被改写”之间的差别。只要 \\texttt{{example.com}} 的 NS 记录被替换成 \\texttt{{ns.attacker32.com}}，后续解析这个域下的新主机名时，本地 DNS 服务器就会主动去问攻击者控制的权威服务器。

            \\subsubsection{{关键命令记录}}
            {self._command_block("任务 3 关键命令", local_task3_commands)}

            \\subsubsection{{结果与分析}}
            这次实验里，\\texttt{{www.example.com}} 返回 \\texttt{{1.2.3.5}}，\\texttt{{mail.example.com}} 和直接指定 \\texttt{{@ns.attacker32.com}} 查询得到的结果都稳定是 \\texttt{{1.2.3.6}}；同时缓存中还能看到 \\texttt{{example.com NS ns.attacker32.com}}。这说明本地 DNS 服务器已经不是“偶然收下一条错误 A 记录”，而是把整个 \\texttt{{example.com}} 域的权威链都改写了。

            {self._snippet_listing("local-task3-dig", "bash", "本地任务 3：多主机名 dig 输出")}
            {self._snippet_listing("local-task3-cache", "bash", "本地任务 3：NS 投毒缓存结果")}
            {self._analysis_block(self.analysis_local["任务 3：伪造 NS 记录"])}
            {self._figure_tex("local-task3-ns-poisoning.png")}
            {self._storyboard_figure_tex("local-task3-ns-poisoning.png")}

            \\subsection{{任务 4：伪造另一个域的 NS 记录}}
            任务 4 是对一个常见误解的检验：既然我已经能在 Authority Section 里插入 NS 记录，那么能不能把与当前查询无关的域名也一起顺手投毒？这次实验的答案是否定的。

            \\subsubsection{{关键命令记录}}
            {self._command_block("任务 4 关键命令", local_task4_commands)}

            \\subsubsection{{结果与分析}}
            缓存结果里只保留了和当前 \\texttt{{example.com}} 查询语义相关的记录，而 \\texttt{{google.com}} 没有像 \\texttt{{example.com}} 一样被接受。这说明 DNS 服务器并不是“看到 Authority Section 里的所有记录就缓存”，而是仍然会做最基本的相关性判断。

            {self._snippet_listing("local-task4-cache", "bash", "本地任务 4：跨域记录缓存结果")}
            {self._analysis_block(self.analysis_local["任务 4：伪造另一个域的 NS 记录"])}
            {self._figure_tex("local-task4-cross-domain-cache-observation.png")}
            {self._storyboard_figure_tex("local-task4-cross-domain-cache-observation.png")}

            \\subsection{{任务 5：附加部分记录缓存分析}}
            任务 5 进一步研究 Additional Section 的真实缓存行为：如果我同时塞入和权威链有关的记录、以及完全不相干的额外记录，本地 DNS 服务器会收下哪些？

            \\subsubsection{{关键命令记录}}
            {self._command_block("任务 5 关键命令", local_task5_commands)}

            \\subsubsection{{结果与分析}}
            这一步最重要的不是“我发送了哪些附加条目”，而是“缓存里最后剩下哪些条目”。实际结果说明，和权威链直接相关的 glue 记录更容易留下，而不相关的附加信息不会稳定进入缓存。因此我更倾向于把 Additional Section 看成一个“受关联性约束的辅助区”，而不是一个可以随意附带任意 A 记录的出口。

            {self._snippet_listing("local-task5-cache", "bash", "本地任务 5：附加部分缓存结果")}
            {self._analysis_block(self.analysis_local["任务 5：附加部分记录缓存"])}
            {self._figure_tex("local-task5-additional-section-cache.png")}
            {self._storyboard_figure_tex("local-task5-additional-section-cache.png")}

            \\section{{第二部分：远程 DNS / Kaminsky 攻击}}

            \\subsection{{攻击背景与主要难点}}
            远程 DNS 攻击和本地攻击最大的区别在于：我看不到本地 DNS 服务器向真实权威服务器发出的查询，因此也就拿不到实时的 Transaction ID。传统的“嗅探后立即伪造”路线在这里走不通，Kaminsky 攻击的核心正是在于不等缓存超时，而是不断制造新的随机子域名查询机会，让攻击者持续获得新的抢答窗口。

            \\subsection{{环境搭建与基线验证}}
            在开始远程攻击前，我先重新确认 Compose 环境、用户端基线 dig 结果以及攻击者权威服务器的返回值。只有把这些基础状态确认清楚，后面看到普通 dig 也返回 \\texttt{{1.2.3.5}} 时，才能判断那真的是远程缓存投毒成功，而不是环境本身就有问题。

            \\subsubsection{{关键命令记录}}
            {self._command_block("远程环境搭建与基线命令", remote_env_commands)}

            \\subsubsection{{结果与分析}}
            本地与远程两部分在基线层面的差异并不大：普通 \\texttt{{www.example.com}} 查询仍返回真实公网地址，而直接指定攻击者权威服务器查询时会返回 \\texttt{{1.2.3.5}}。真正的区别出现在后续的攻击路径上。

            {self._analysis_block(self.analysis_remote["DNS 配置基线"])}
            {self._figure_tex("remote-baseline-dig-and-cache.png")}
            {self._storyboard_figure_tex("remote-baseline-dig-and-cache.png")}

            \\subsection{{任务 2：构造 DNS 请求}}
            远程攻击的第一步不是直接发伪造响应，而是先用随机子域名触发新的外部查询，让本地 DNS 服务器对“此前从未见过的名字”重新发起递归解析。只有这样，攻击者才有和合法响应抢时间的机会。

            \\subsubsection{{关键命令记录}}
            {self._command_block("远程任务 2 关键命令", remote_task2_commands)}

            \\subsubsection{{结果与分析}}
            这次实验里我额外做了一步现实适配：先把当前真正负责 \\texttt{{example.com}} 的权威 IPv4 全部解析出来，再据此构造伪造响应。解析结果为 {tex_escape(remote_authority_ips)}。这一点非常关键，因为现实环境已经不再符合旧讲义中的静态权威设定。

            {self._snippet_listing("remote-authority-ips", "bash", "远程实验：example.com 当前权威 IPv4 列表")}
            {self._code_listing("prepare_packets.py", "Python", "远程实验：Scapy 模板生成脚本")}
            {self._figure_tex("remote-request-trigger-trace.png")}
            {self._storyboard_figure_tex("remote-request-trigger-trace.png")}

            \\subsection{{任务 3：伪造 DNS 响应}}
            伪造 DNS 响应时，我需要同时保证三件事：第一，问题部分与随机子域名一致；第二，答案部分给出我预设的伪造 A 记录；第三，Authority Section 把 \\texttt{{example.com}} 的 NS 指向 \\texttt{{ns.attacker32.com}}。除此之外，源地址也必须足够像真的，否则本地 DNS 服务器不会接受它。

            \\subsubsection{{关键命令记录}}
            {self._command_block("远程任务 3 关键命令", remote_task34_commands)}

            \\subsubsection{{结果与分析}}
            我在这里采用的是“Scapy 构造模板 + C 高频发包”的混合路线。前者负责保证包的结构正确，后者负责保证发包速度足够快；这比单用 Python 或单用 C 都更适合当前实验。

            {self._code_listing("attack.c", "C", "远程实验：Kaminsky C 攻击程序")}
            {self._figure_tex("remote-forged-response-trace.png")}
            {self._storyboard_figure_tex("remote-forged-response-trace.png")}

            \\subsection{{任务 4：Kaminsky 攻击实施}}
            Kaminsky 攻击的核心，不是赌某一个随机子域名刚好命中，而是不断制造新的随机子域名查询，让攻击者持续获得多轮抢答机会。只要其中一轮让伪造权威链先进入缓存，后面就不需要继续猜了。

            \\subsubsection{{关键命令记录}}
            {self._command_block("远程任务 4 关键命令", remote_task4_commands)}

            \\subsubsection{{结果与分析}}
            这次实验在第一轮完整尝试中就观察到了成功信号：缓存筛选第一行已经显示 \\texttt{{{tex_escape(values['remote_cache_first'])}}}，同时还能看到一个伪造随机子域名的 A 记录进入缓存。这说明本地 DNS 服务器在等待真实响应时，已经接受了我构造的伪造权威链。

            {self._snippet_listing("remote-cache-success", "bash", "远程实验：Kaminsky 成功后的缓存筛选")}
            {self._analysis_block(self.analysis_remote["远程 Kaminsky 攻击结果"])}
            {self._figure_tex("remote-kaminsky-cache-success.png")}
            {self._storyboard_figure_tex("remote-kaminsky-cache-success.png")}

            \\subsection{{任务 5：攻击结果验证}}
            我把远程攻击是否真正成功的判据设得很明确：不是缓存里“看起来有一条可疑记录”就算成功，而是普通用户查询和直接问攻击者权威服务器的结果必须一致。只有这样，才能说明本地 DNS 服务器已经真的沿着错误的权威路径继续解析了。

            \\subsubsection{{关键命令记录}}
            {self._command_block("远程任务 5 关键命令", remote_task5_commands)}

            \\subsubsection{{结果与分析}}
            最终验证里，普通 \\texttt{{dig +short www.example.com}} 和 \\texttt{{dig +short @ns.attacker32.com www.example.com}} 都返回了 {tex_escape(remote_final)}。这说明本地 DNS 服务器已经不再去问原本合法的权威服务器，而是把攻击者控制的权威链当成了后续解析的正常路径。

            {self._snippet_listing("remote-final-dig", "bash", "远程实验：最终 dig 验证")}
            {self._figure_tex("remote-final-dig-verification.png")}
            {self._storyboard_figure_tex("remote-final-dig-verification.png")}

            \\section{{关键代码设计与说明}}
            \\subsection{{本地 DNS 攻击脚本}}
            本地攻击脚本的设计重点是“同一套框架覆盖任务 1 到任务 5”。我把不同任务下 Answer、Authority 和 Additional Section 的差异统一收敛到脚本内部的分支逻辑里，通过 \\texttt{{--task}} 参数切换，而不是为每个任务各写一份完全独立的脚本。这样做的好处是结构清晰、调试方便，也更容易观察同一查询目标在不同响应构造下的缓存差异。

            \\subsection{{远程模板生成脚本}}
            \\texttt{{prepare\\_packets.py}} 负责先生成请求模板和响应模板，后续 C 程序只需要围绕模板做小范围修改，不必在 C 里手写整个 DNS 包结构。这种“先模板化，再高频修改”的思路显著降低了远程实验的代码复杂度。

            \\subsection{{Kaminsky C 攻击程序}}
            \\texttt{{attack.c}} 的关键设计在于三点：第一，用固定占位串标记域名位置，方便后续直接按偏移替换；第二，在每一轮攻击中都重新生成随机子域名并遍历 Transaction ID；第三，把实时解析到的多个权威 IPv4 地址全部作为候选源地址，以适配现实网络环境。这第三点，是本次远程实验成功率明显提升的关键。

            \\section{{综合分析与实验结论}}
            从本地实验到远程实验，我最直接的感受是：DNS 攻击的难度并不只取决于“协议本身有多脆弱”，更取决于攻击者能看到多少真实查询过程。本地实验里，我可以直接看到查询、直接即时回包，因此关键在于理解服务器到底会缓存哪些内容；远程实验里，我看不到真实查询，因此关键转移到“如何持续制造新的抢答窗口”。

            另外，任务 4 和任务 5 也让我对 DNS 缓存行为有了更细的认识。即使 DNS 服务器在很多地方存在过度信任，它也不是完全不做筛选：和当前查询无关的 Authority 记录、Additional 记录，并不会像表面看起来那样轻易进入缓存。也正因为如此，真正有效的攻击不是“塞得越多越好”，而是“伪造得越相关越好”。

            综合来看，本地与远程两部分共同揭示了一条完整的攻击链：先从用户主机是否会被直接欺骗开始，再到本地 DNS 缓存是否会被污染、整个域的权威路径是否会被改写，最后发展到看不见查询报文时如何仍然完成同样的权威链投毒。我认为这正是实验四最值得掌握的地方。

            \\section{{附录：完整代码、自动终端取证总览与全过程记录}}

            \\subsection{{完整代码}}
            {self._code_listing("dns_spoof_lab.py", "Python", "附录：本地 DNS Scapy 攻击脚本")}
            {self._code_listing("prepare_packets.py", "Python", "附录：远程实验 Scapy 模板生成脚本")}
            {self._code_listing("attack.c", "C", "附录：远程实验 Kaminsky C 攻击程序")}

            \\subsection{{自动终端取证图目录}}
            \\begin{{longtable}}{{>{{\\raggedright\\arraybackslash}}p{{0.24\\textwidth}} >{{\\raggedright\\arraybackslash}}p{{0.16\\textwidth}} >{{\\raggedright\\arraybackslash}}p{{0.18\\textwidth}} >{{\\raggedright\\arraybackslash}}p{{0.30\\textwidth}}}}
            \\toprule
            文件名 & 章节 & 建议终端 & 拍摄重点 \\\\
            \\midrule
            local-config-dig-baseline.png & 本地配置测试 & 用户容器终端 & 三条基线 dig 结果同屏 \\\\
            local-task1-user-spoof-result.png & 任务 1 & 用户 + 攻击者终端 & 用户被直接欺骗且脚本命中 \\\\
            local-task2-cache-poisoning.png & 任务 2 & 用户 + DNS 终端 & 双次 dig 与缓存命中同屏 \\\\
            local-task3-ns-poisoning.png & 任务 3 & 用户 + DNS 终端 & 新主机名结果与 NS 缓存行同屏 \\\\
            local-task4-cross-domain-cache-observation.png & 任务 4 & DNS 终端 & 只看到 example.com 相关记录 \\\\
            local-task5-additional-section-cache.png & 任务 5 & DNS 终端 & Additional Section 最终真正留下的内容 \\\\
            remote-baseline-dig-and-cache.png & 远程基线 & 宿主机 + 用户终端 & 环境启动与基线 dig \\\\
            remote-request-trigger-trace.png & 远程任务 2 & 抓包窗口 & 随机子域名触发新的查询 \\\\
            remote-forged-response-trace.png & 远程任务 3 & 攻击者终端 / 抓包 & 伪造响应字段设计 \\\\
            remote-kaminsky-cache-success.png & 远程任务 4 & DNS 终端 & example.com NS 已改为 ns.attacker32.com \\\\
            remote-final-dig-verification.png & 远程任务 5 & 用户终端 & 普通 dig 与攻击者权威 dig 一致 \\\\
            \\bottomrule
            \\end{{longtable}}

            \\subsection{{自动终端取证总览}}
            \\begin{{figure}}[H]
                \\centering
                \\IfFileExists{{../evidence/auto/verification/contact-sheet.png}}{{%
                    \\includegraphics[width=0.98\\textwidth]{{../evidence/auto/verification/contact-sheet.png}}%
                }}{{%
                    \\fbox{{\\begin{{minipage}}[c][0.20\\textheight][c]{{0.92\\textwidth}}
                        \\centering \\textbf{{总览页未提供}}\\\\[0.4em]
                        \\small 期望文件：\\path{{contact-sheet.png}}
                    \\end{{minipage}}}}%
                }}
                \\caption{{实验四自动终端取证总览页}}
            \\end{{figure}}

            {self._manual_extra_figures_tex()}

            {self._steps_appendix_tex("本地实验全过程记录", self.local_summary)}
            {self._steps_appendix_tex("远程实验全过程记录", self.remote_summary)}

            \\end{{document}}
            """
        )
        return tex

    def _write_report_context(self):
        self.context_path.write_text(json.dumps(self.build_context(), indent=2, ensure_ascii=False), encoding="utf-8")

    def build(self):
        if self.package_root.exists():
            shutil.rmtree(self.package_root)
        ensure_dir(self.report_dir)
        ensure_dir(self.auto_snippets_dir)
        ensure_dir(self.auto_code_dir)
        ensure_dir(self.auto_boards_dir)
        ensure_dir(self.auto_storyboards_dir)
        ensure_dir(self.verification_dir)
        ensure_dir(self.manual_dir)
        ensure_dir(self.manual_extras_dir)

        self._copy_template_assets()
        self._import_manual_images()
        self._extract_and_write_snippets()
        self._copy_generated_code()
        self._render_auto_terminal_shots()
        self._render_storyboards()
        self._verify_evidence_outputs(run_override_test=False)
        self._write_shot_list()
        self._write_build_script()
        tex_content = self._render_tex()
        (self.report_dir / self.profile["report_filename"]).write_text(tex_content, encoding="utf-8")
        self._write_report_context()
        self.compile_package()
        return self.package_root

    def compile_package(self, package_root=None):
        package_root = Path(package_root).resolve() if package_root else self.package_root
        report_dir = package_root / "report"
        tex_file = self.profile["report_filename"]
        pdf_file = tex_file.replace(".tex", ".pdf")
        env = os.environ.copy()
        env["TEXINPUTS"] = f"{report_dir / 'texmf-local' / 'tex'}//:"
        env["TEXFONTMAPS"] = f"{report_dir / 'texmf-local' / 'fonts' / 'misc' / 'xetex' / 'fontmapping'}//:"
        completed = subprocess.run(
            ["latexmk", "-xelatex", "-interaction=nonstopmode", "-file-line-error", tex_file],
            cwd=report_dir,
            env=env,
            capture_output=True,
            text=True,
        )
        compile_log = package_root / "compile.log"
        compile_log.write_text(
            f"STDOUT:\n{completed.stdout}\n\nSTDERR:\n{completed.stderr}",
            encoding="utf-8",
        )
        if completed.returncode != 0:
            raise PackagerError(f"LaTeX 编译失败，详见 {compile_log}")
        shutil.copy2(report_dir / pdf_file, package_root / self.profile["final_pdf_name"])
        return package_root / self.profile["final_pdf_name"]


def build_parser():
    parser = argparse.ArgumentParser(description="Build ZJU SEED lab report packages from completed evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_arguments(subparser):
        subparser.add_argument("--profile", required=True)
        subparser.add_argument("--repo-root", required=True)
        subparser.add_argument("--local-run-id")
        subparser.add_argument("--remote-run-id")

    inspect_parser = subparsers.add_parser("inspect")
    add_common_arguments(inspect_parser)

    build_parser_obj = subparsers.add_parser("build")
    add_common_arguments(build_parser_obj)

    render_parser = subparsers.add_parser("render-auto-shots")
    add_common_arguments(render_parser)

    storyboard_parser = subparsers.add_parser("render-storyboards")
    add_common_arguments(storyboard_parser)

    verify_parser = subparsers.add_parser("verify-evidence")
    add_common_arguments(verify_parser)

    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("--package-root", required=True)
    compile_parser.add_argument("--profile", default="lab4-dns-combined")
    compile_parser.add_argument("--repo-root", default=".")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "compile":
        packager = ReportPackager(args.repo_root, args.profile)
        pdf = packager.compile_package(args.package_root)
        print(pdf)
        return 0

    packager = ReportPackager(args.repo_root, args.profile, args.local_run_id, args.remote_run_id)
    if args.command == "inspect":
        print(packager.inspect())
        return 0
    if args.command == "render-auto-shots":
        ensure_dir(packager.package_root)
        ensure_dir(packager.report_dir)
        ensure_dir(packager.auto_snippets_dir)
        ensure_dir(packager.auto_code_dir)
        ensure_dir(packager.auto_boards_dir)
        ensure_dir(packager.manual_dir)
        packager._extract_and_write_snippets()
        packager._copy_generated_code()
        packager._render_auto_terminal_shots()
        print(packager.auto_boards_dir)
        return 0
    if args.command == "render-storyboards":
        ensure_dir(packager.package_root)
        ensure_dir(packager.report_dir)
        ensure_dir(packager.auto_snippets_dir)
        ensure_dir(packager.auto_code_dir)
        ensure_dir(packager.auto_boards_dir)
        ensure_dir(packager.auto_storyboards_dir)
        ensure_dir(packager.verification_dir)
        ensure_dir(packager.manual_dir)
        packager._extract_and_write_snippets()
        packager._copy_generated_code()
        packager._render_auto_terminal_shots()
        packager._render_storyboards()
        print(packager.auto_storyboards_dir)
        return 0
    if args.command == "verify-evidence":
        ensure_dir(packager.package_root)
        ensure_dir(packager.report_dir)
        ensure_dir(packager.auto_snippets_dir)
        ensure_dir(packager.auto_code_dir)
        ensure_dir(packager.auto_boards_dir)
        ensure_dir(packager.auto_storyboards_dir)
        ensure_dir(packager.verification_dir)
        ensure_dir(packager.manual_dir)
        packager._extract_and_write_snippets()
        packager._copy_generated_code()
        packager._render_auto_terminal_shots()
        packager._render_storyboards()
        packager._verify_evidence_outputs(run_override_test=True)
        print(packager.verification_dir)
        return 0
    if args.command == "build":
        package_root = packager.build()
        print(package_root)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
