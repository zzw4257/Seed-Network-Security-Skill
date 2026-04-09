from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from masfactory.visualizer.serialize import serialize_root_graph


STAGE_ORDER = [
    ("runner_preflight", "实验预检"),
    ("runner_execute", "实验执行"),
    ("report_package", "报告打包"),
    ("manual_ui", "人工收尾界面"),
    ("verify", "证据校验"),
]


def _load_summary_dict(output: dict[str, Any]) -> dict[str, Any]:
    if isinstance(output.get("studio_summary_data"), dict):
        return dict(output["studio_summary_data"])
    payload = output.get("studio_summary")
    if isinstance(payload, str) and payload.strip():
        return json.loads(payload)
    if isinstance(payload, dict):
        return dict(payload)
    return dict(output)


def _to_rel_href(base_dir: Path, target: Path | None) -> str:
    if target is None:
        return ""
    rel = os.path.relpath(target, base_dir)
    return quote(rel.replace(os.sep, "/"), safe="/:@#?=&")


def _package_files(package_root: Path | None) -> dict[str, str]:
    if package_root is None or not package_root.exists():
        return {}
    pdfs = sorted(package_root.glob("*.pdf"))
    report_context = package_root / "report-context.json"
    tex_file = package_root / "report" / "lab4_dns_report.tex"
    shot_list = package_root / "evidence" / "manual" / "SHOT_LIST.md"
    return {
        "pdf": str(pdfs[0]) if pdfs else "",
        "report_context": str(report_context) if report_context.exists() else "",
        "tex": str(tex_file) if tex_file.exists() else "",
        "shot_list": str(shot_list) if shot_list.exists() else "",
    }


def _status_badge(status: str) -> str:
    palette = {
        "ok": ("#e8f7ed", "#17663a"),
        "launched": ("#e9f3ff", "#1356a8"),
        "skipped": ("#eef1f4", "#51606f"),
        "failed": ("#ffe9e7", "#a63328"),
    }
    bg, fg = palette.get(status or "", ("#eef1f4", "#51606f"))
    label = html.escape(status or "unknown")
    return f"<span class='badge' style='background:{bg};color:{fg};'>{label}</span>"


def _render_stage_blocks(summary: dict[str, Any]) -> str:
    stages = summary.get("stages") or {}
    blocks: list[str] = []
    for stage_key, title in STAGE_ORDER:
        stage = stages.get(stage_key) or {}
        if not stage:
            continue
        status = _status_badge(str(stage.get("status") or "unknown"))
        command = html.escape(str(stage.get("command") or "")).strip()
        output = html.escape(str(stage.get("output") or "")).strip()
        extra_rows: list[str] = []
        for extra_key, label in (
            ("inspect_command", "inspect 命令"),
            ("build_command", "build 命令"),
            ("url", "UI 地址"),
            ("pid", "PID"),
            ("log", "UI 日志"),
            ("pdf", "PDF"),
            ("verification_dir", "校验目录"),
        ):
            value = str(stage.get(extra_key) or "").strip()
            if value:
                extra_rows.append(
                    f"<div class='meta-line'><span>{html.escape(label)}</span><code>{html.escape(value)}</code></div>"
                )
        blocks.append(
            f"""
            <section class="stage-card">
              <div class="stage-head">
                <h3>{html.escape(title)}</h3>
                {status}
              </div>
              {"".join(extra_rows)}
              {f"<div class='section-label'>命令</div><pre>{command}</pre>" if command else ""}
              {f"<div class='section-label'>输出摘要</div><pre>{output}</pre>" if output else ""}
            </section>
            """
        )
    return "".join(blocks)


def _render_graph_lane(graph_payload: dict[str, Any]) -> str:
    nodes = graph_payload.get("nodes") or []
    pieces = []
    for index, node in enumerate(nodes):
        pieces.append(f"<div class='graph-node'>{html.escape(str(node))}</div>")
        if index < len(nodes) - 1:
            pieces.append("<div class='graph-arrow'>→</div>")
    return "".join(pieces)


def _render_edges(graph_payload: dict[str, Any]) -> str:
    edges = graph_payload.get("edges") or []
    if not edges:
        return "<div class='muted'>无边信息。</div>"
    rows = []
    for edge in edges:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(edge.get('sender', '')))}</td>"
            f"<td>{html.escape(str(edge.get('receiver', '')))}</td>"
            f"<td>{html.escape(json.dumps(edge.get('keys', {}), ensure_ascii=False))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>发送节点</th><th>接收节点</th><th>Keys</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _build_dashboard_html(run_dir: Path, summary: dict[str, Any], graph_payload: dict[str, Any]) -> str:
    package_root = Path(summary["package_root"]).resolve() if summary.get("package_root") else None
    package_files = _package_files(package_root)
    pdf_path = Path(package_files["pdf"]).resolve() if package_files.get("pdf") else None
    report_context_path = Path(package_files["report_context"]).resolve() if package_files.get("report_context") else None
    tex_path = Path(package_files["tex"]).resolve() if package_files.get("tex") else None
    shot_list_path = Path(package_files["shot_list"]).resolve() if package_files.get("shot_list") else None
    verification_dir = Path(summary["verification_dir"]).resolve() if summary.get("verification_dir") else None
    route_summary = html.escape(str(summary.get("route_summary") or ""))
    ui_url = html.escape(str(summary.get("manual_ui_url") or ""))
    package_root_text = html.escape(str(package_root)) if package_root else "未生成"
    links = []
    for label, target in (
        ("PDF 成品", pdf_path),
        ("report-context.json", report_context_path),
        ("TeX 主文件", tex_path),
        ("SHOT_LIST.md", shot_list_path),
        ("证据校验目录", verification_dir),
    ):
        if target and target.exists():
            links.append(
                f"<a href='{_to_rel_href(run_dir, target)}' target='_blank'>{html.escape(label)}</a>"
            )
    artifact_links = []
    for label, name in (
        ("summary.json", "summary.json"),
        ("graph.json", "graph.json"),
        ("dashboard.html", "dashboard.html"),
    ):
        artifact_links.append(f"<a href='{quote(name)}' target='_blank'>{html.escape(label)}</a>")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>ZJU SEED Lab Studio</title>
  <style>
    :root {{
      --bg: #f4f6f9;
      --panel: #ffffff;
      --line: #d8dee6;
      --text: #17212b;
      --muted: #5f6b76;
      --accent: #0f6f91;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1520px;
      margin: 0 auto;
      padding: 24px;
    }}
    .hero, .panel, .stage-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }}
    .hero {{
      padding: 24px;
      margin-bottom: 20px;
    }}
    h1, h2, h3 {{
      margin: 0;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }}
    .chip, .badge {{
      display: inline-flex;
      align-items: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
    }}
    .chip {{
      background: #eef6fa;
      color: #0e5f7c;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .panel {{
      padding: 20px;
    }}
    .panel h2 {{
      margin-bottom: 12px;
      font-size: 18px;
    }}
    .muted {{
      color: var(--muted);
      line-height: 1.6;
    }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }}
    .meta-list {{
      display: grid;
      gap: 10px;
    }}
    .meta-line {{
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 14px;
    }}
    code, pre {{
      font-family: "SFMono-Regular", Menlo, Monaco, monospace;
      font-size: 13px;
    }}
    code {{
      background: #f4f7fa;
      padding: 3px 6px;
      border-radius: 8px;
      word-break: break-all;
    }}
    .graph-lane {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin-top: 8px;
    }}
    .graph-node {{
      padding: 10px 14px;
      border-radius: 12px;
      background: #f8fbfd;
      border: 1px solid #d8e7ef;
      font-weight: 700;
      color: #134d63;
    }}
    .graph-arrow {{
      font-size: 24px;
      color: #7c91a0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid #e8edf2;
      vertical-align: top;
      word-break: break-word;
    }}
    .stages {{
      display: grid;
      gap: 16px;
    }}
    .stage-card {{
      padding: 18px;
    }}
    .stage-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .section-label {{
      margin: 14px 0 8px 0;
      color: var(--muted);
      font-weight: 700;
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid #e6ebf0;
      background: #fbfcfd;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.55;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>ZJU SEED Lab Studio</h1>
      <div class="muted">这个页面是 MASFactory 增强分支的展示工件，用来把实验主线、报告打包链路、人工收尾入口和校验结果收拢到一个本地可浏览页面中。</div>
      <div class="hero-meta">
        <span class="chip">workflow_mode: {html.escape(str(summary.get("workflow_mode") or ""))}</span>
        <span class="chip">route_mode: {html.escape(str(summary.get("route_mode") or ""))}</span>
        <span class="chip">report_profile: {html.escape(str(summary.get("report_profile") or ""))}</span>
        <span class="chip">graph_mode: {html.escape(str(summary.get("graph_mode") or ""))}</span>
      </div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>当前路线与产物</h2>
        <div class="muted">{route_summary}</div>
        <div class="meta-list" style="margin-top:14px;">
          <div class="meta-line"><span>Package Root</span><code>{package_root_text}</code></div>
          {f"<div class='meta-line'><span>Manual UI</span><code>{ui_url}</code></div>" if ui_url else ""}
        </div>
        <div class="links">
          {"".join(links) if links else "<span class='muted'>当前没有可点击的产物链接。</span>"}
        </div>
        <div class="links" style="margin-top:10px;">
          {"".join(artifact_links)}
        </div>
      </div>
      <div class="panel">
        <h2>Graph 快照</h2>
        <div class="graph-lane">{_render_graph_lane(graph_payload)}</div>
        <div class="section-label">边连接</div>
        {_render_edges(graph_payload)}
      </div>
    </section>
    <section class="stages">
      {_render_stage_blocks(summary)}
    </section>
  </div>
</body>
</html>"""


def export_run_artifacts(
    *,
    graph: Any,
    output: dict[str, Any],
    app_root: Path,
    workspace_root: Path,
    graph_mode: str,
) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    runs_dir = app_root / "runs"
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = _load_summary_dict(output)
    summary["workspace_root"] = str(workspace_root)
    summary["graph_mode"] = graph_mode

    graph_payload = serialize_root_graph(graph).graph
    dashboard_html = _build_dashboard_html(run_dir, summary, graph_payload)

    summary_path = run_dir / "summary.json"
    graph_path = run_dir / "graph.json"
    dashboard_path = run_dir / "dashboard.html"
    readme_path = run_dir / "README.md"

    summary["artifacts"] = {
        "run_dir": str(run_dir),
        "summary_json": str(summary_path),
        "graph_json": str(graph_path),
        "dashboard_html": str(dashboard_path),
        "notes_md": str(readme_path),
    }

    summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
    graph_json = json.dumps(graph_payload, ensure_ascii=False, indent=2)
    summary_path.write_text(summary_json, encoding="utf-8")
    graph_path.write_text(graph_json, encoding="utf-8")
    dashboard_path.write_text(dashboard_html, encoding="utf-8")
    readme_path.write_text(
        "\n".join(
            [
                "# ZJU SEED Lab Studio Run",
                "",
                f"- run_dir: `{run_dir}`",
                f"- summary: `{summary_path}`",
                f"- graph: `{graph_path}`",
                f"- dashboard: `{dashboard_path}`",
            ]
        ),
        encoding="utf-8",
    )

    compatibility_path = runs_dir / f"{timestamp}.json"
    compatibility_path.write_text(summary_json, encoding="utf-8")
    (runs_dir / "latest.json").write_text(summary_json, encoding="utf-8")
    (runs_dir / "latest-graph.json").write_text(graph_json, encoding="utf-8")
    (runs_dir / "latest-dashboard.html").write_text(dashboard_html, encoding="utf-8")

    return summary
