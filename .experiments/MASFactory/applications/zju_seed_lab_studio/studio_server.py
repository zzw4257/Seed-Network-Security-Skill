from __future__ import annotations

import argparse
import html
import json
import os
import re
import socket
import subprocess
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_ROOT = Path(__file__).resolve().parent
RUNS_ROOT = APP_ROOT / "runs"
MAIN_SCRIPT = APP_ROOT / "main.py"


def find_available_port(host: str, preferred_port: int, search_limit: int = 40) -> int:
    for port in range(preferred_port, preferred_port + search_limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"无法在 {preferred_port}-{preferred_port + search_limit - 1} 范围内找到可用端口")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_startup_lines(log_path: Path, *, max_lines: int = 4, timeout_s: float = 2.0) -> list[str]:
    lines: list[str] = []
    deadline = time.monotonic() + timeout_s
    while len(lines) < max_lines and time.monotonic() < deadline:
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="ignore")
            lines = [line.strip() for line in content.splitlines() if line.strip()][:max_lines]
            if lines:
                break
        time.sleep(0.1)
    return lines


def process_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".html":
        return "text/html; charset=utf-8"
    if suffix == ".json":
        return "application/json; charset=utf-8"
    if suffix == ".md":
        return "text/markdown; charset=utf-8"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".tex":
        return "text/plain; charset=utf-8"
    return "application/octet-stream"


@dataclass
class JobState:
    job_id: str
    created_at: str
    params: dict[str, Any]
    status: str = "running"
    process_pid: int | None = None
    returncode: int | None = None
    log_path: str = ""
    output_lines: list[str] = field(default_factory=list)
    summary: dict[str, Any] | None = None
    error: str = ""

    def tail(self, max_lines: int = 60) -> str:
        return "\n".join(self.output_lines[-max_lines:])

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "created_at": self.created_at,
            "params": self.params,
            "status": self.status,
            "process_pid": self.process_pid,
            "returncode": self.returncode,
            "log_path": self.log_path,
            "tail": self.tail(),
            "summary": self.summary,
            "error": self.error,
        }


@dataclass
class ManualUiState:
    status: str = "inactive"
    pid: int | None = None
    url: str = ""
    port: str = ""
    log_path: str = ""
    package_root: str = ""
    output: str = ""
    command: str = ""

    def to_dict(self) -> dict[str, Any]:
        alive = process_alive(self.pid)
        status = self.status
        if status == "running" and not alive:
            status = "stopped"
        return {
            "status": status,
            "pid": self.pid,
            "url": self.url,
            "port": self.port,
            "log_path": self.log_path,
            "package_root": self.package_root,
            "output": self.output,
            "command": self.command,
            "alive": alive,
        }


class StudioRuntime:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.jobs_dir = RUNS_ROOT / "_studio_jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.ui_dir = RUNS_ROOT / "_studio_manual_ui"
        self.ui_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._jobs: dict[str, JobState] = {}
        self._latest_job_id: str | None = None
        self._manual_ui = ManualUiState()

    def start_job(self, params: dict[str, Any]) -> JobState:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        job_id = f"job-{timestamp}"
        log_path = self.jobs_dir / f"{job_id}.log"
        command = [
            "python",
            "-u",
            str(MAIN_SCRIPT),
            "--workspace-root",
            str(self.workspace_root),
            "--workflow-mode",
            str(params["workflow_mode"]),
            "--route-mode",
            str(params["route_mode"]),
            "--report-profile",
            str(params["report_profile"]),
            "--runner-profile",
            str(params["runner_profile"]),
            "--graph-mode",
            str(params["graph_mode"]),
        ]
        if params.get("launch_ui"):
            command.extend(["--launch-ui", "--ui-port", str(params["ui_port"])])
        job = JobState(
            job_id=job_id,
            created_at=datetime.now().isoformat(timespec="seconds"),
            params={**params, "command": " ".join(command)},
            log_path=str(log_path),
        )
        process = subprocess.Popen(
            command,
            cwd=self.workspace_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        job.process_pid = process.pid
        with self._lock:
            self._jobs[job_id] = job
            self._latest_job_id = job_id
        thread = threading.Thread(
            target=self._collect_job_output,
            args=(job_id, process, log_path),
            daemon=True,
            name=f"studio-job-{job_id}",
        )
        thread.start()
        return job

    def _collect_job_output(self, job_id: str, process: subprocess.Popen[str], log_path: Path) -> None:
        buffer: list[str] = []
        with log_path.open("w", encoding="utf-8") as log_file:
            if process.stdout:
                for line in process.stdout:
                    log_file.write(line)
                    log_file.flush()
                    clean = line.rstrip("\n")
                    buffer.append(clean)
                    with self._lock:
                        job = self._jobs.get(job_id)
                        if job:
                            job.output_lines.append(clean)
            returncode = process.wait()
        summary = self._parse_json_tail(buffer)
        with self._lock:
            job = self._jobs[job_id]
            job.returncode = returncode
            job.summary = summary
            if returncode == 0:
                job.status = "completed"
            else:
                job.status = "failed"
                job.error = "workflow 命令返回非零退出码"

    def _parse_json_tail(self, lines: list[str]) -> dict[str, Any] | None:
        text = "\n".join(lines).strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
        return None

    def get_job(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def latest_job(self) -> JobState | None:
        with self._lock:
            if not self._latest_job_id:
                return None
            return self._jobs.get(self._latest_job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda item: item.created_at, reverse=True)
        return [job.to_dict() for job in jobs]

    def latest_run_summary(self) -> dict[str, Any] | None:
        latest_path = RUNS_ROOT / "latest.json"
        if not latest_path.exists():
            return None
        try:
            return read_json(latest_path)
        except Exception:
            return None

    def latest_dashboard_path(self) -> Path | None:
        summary = self.latest_run_summary()
        if not summary:
            return None
        dashboard = summary.get("artifacts", {}).get("dashboard_html")
        if not dashboard:
            return None
        path = Path(dashboard)
        return path if path.exists() else None

    def latest_package_root(self) -> Path | None:
        summary = self.latest_run_summary()
        if summary and summary.get("package_root"):
            path = Path(str(summary["package_root"])).resolve()
            if path.exists():
                return path
        return None

    def manual_ui_state(self) -> dict[str, Any]:
        with self._lock:
            return self._manual_ui.to_dict()

    def start_manual_ui(self, *, package_root: Path | None = None, preferred_port: int = 8765) -> dict[str, Any]:
        package_root = (package_root or self.latest_package_root() or (self.workspace_root / "report-packages" / "lab4-dns-combined")).resolve()
        if not package_root.exists():
            raise FileNotFoundError(f"package_root 不存在: {package_root}")
        script = self.workspace_root / "skills" / "zju-seed-report-packager" / "scripts" / "manual_evidence_ui.py"
        if not script.exists():
            raise FileNotFoundError(f"manual_evidence_ui.py 不存在: {script}")
        with self._lock:
            if self._manual_ui.status == "running" and process_alive(self._manual_ui.pid):
                return self._manual_ui.to_dict()
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        log_path = self.ui_dir / f"manual-ui-{timestamp}.log"
        command = [
            "python",
            "-u",
            str(script),
            "--package-root",
            str(package_root),
            "--repo-root",
            str(self.workspace_root),
            "--port",
            str(preferred_port),
            "--no-open-browser",
        ]
        with log_path.open("w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                command,
                cwd=self.workspace_root,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        startup_lines = read_startup_lines(log_path)
        output = "\n".join(startup_lines) if startup_lines else "Manual UI process started."
        url = ""
        port = ""
        for line in startup_lines:
            match = re.search(r"Manual evidence UI:\s*(http://[^\s]+)", line)
            if match:
                url = match.group(1)
                port = url.rsplit(":", 1)[-1]
                break
        state = ManualUiState(
            status="running",
            pid=process.pid,
            url=url,
            port=port,
            log_path=str(log_path),
            package_root=str(package_root),
            output=output,
            command=" ".join(command),
        )
        with self._lock:
            self._manual_ui = state
        return state.to_dict()


def render_home(runtime: StudioRuntime) -> str:
    latest = runtime.latest_run_summary()
    latest_job = runtime.latest_job()
    latest_dashboard = runtime.latest_dashboard_path()
    manual_ui_state = runtime.manual_ui_state()
    default_params = {
        "workflow_mode": "report_only",
        "route_mode": "reverse_ssh_direct",
        "report_profile": "lab4-dns-combined",
        "runner_profile": "lab4-dns-local",
        "graph_mode": "static",
        "ui_port": 8765,
        "launch_ui": True,
    }
    dashboard_iframe = ""
    latest_dashboard_href = ""
    if latest_dashboard:
        run_dir = latest_dashboard.parent.name
        latest_dashboard_href = f"/runs/{urllib.parse.quote(run_dir)}/dashboard.html"
        dashboard_iframe = f"<iframe class='dashboard-frame' src='{latest_dashboard_href}'></iframe>"
    latest_cards = []
    if latest:
        artifacts = latest.get("artifacts", {})
        latest_cards.extend(
            [
                ("最新 workflow", str(latest.get("workflow_mode") or "")),
                ("最新 route", str(latest.get("route_mode") or "")),
                ("最新 package", str(latest.get("package_root") or "")),
                ("最新 UI", str(latest.get("manual_ui_url") or "")),
                ("最新 PDF", str(latest.get("package_pdf") or "")),
                ("run_dir", str(artifacts.get("run_dir") or "")),
            ]
        )
    latest_rows = "".join(
        f"<div class='meta-row'><span>{html.escape(label)}</span><code>{html.escape(value)}</code></div>"
        for label, value in latest_cards
        if value
    )
    latest_job_block = ""
    if latest_job:
        latest_job_block = f"""
        <section class="panel">
          <h2>最近任务</h2>
          <div class="meta-row"><span>job_id</span><code>{html.escape(latest_job.job_id)}</code></div>
          <div class="meta-row"><span>status</span><code>{html.escape(latest_job.status)}</code></div>
          <div class="meta-row"><span>command</span><code>{html.escape(str(latest_job.params.get('command', '')))}</code></div>
          <pre id="latest-job-tail">{html.escape(latest_job.tail() or '暂无输出')}</pre>
        </section>
        """
    quick_links = []
    if latest_dashboard_href:
        quick_links.append(f"<a href='{latest_dashboard_href}' target='_blank'>打开最新 Dashboard</a>")
    if latest and latest.get("package_pdf"):
        pdf_path = Path(str(latest["package_pdf"]))
        if pdf_path.exists():
            quick_links.append(
                f"<a href='/file?path={urllib.parse.quote(str(pdf_path))}' target='_blank'>打开最新 PDF</a>"
            )
    if latest and latest.get("manual_ui_url"):
        quick_links.append(f"<a href='{html.escape(str(latest['manual_ui_url']))}' target='_blank'>打开 Manual UI</a>")
    latest_manual_ui_url = str(latest.get("manual_ui_url") or "") if latest else ""
    manual_ui_url = str(manual_ui_state.get("url") or latest_manual_ui_url or "")
    manual_ui_iframe = ""
    if manual_ui_url:
        manual_ui_iframe = f"<iframe class='dashboard-frame' src='{html.escape(manual_ui_url)}'></iframe>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>ZJU SEED Lab Studio Server</title>
  <style>
    body {{
      margin: 0;
      background: #f3f5f8;
      color: #17212b;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", sans-serif;
    }}
    .wrap {{
      max-width: 1560px;
      margin: 0 auto;
      padding: 24px;
    }}
    .hero, .panel {{
      background: white;
      border: 1px solid #d8dee6;
      border-radius: 20px;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
    }}
    .hero {{
      padding: 24px;
      margin-bottom: 20px;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 420px 1fr;
      gap: 20px;
      align-items: start;
    }}
    .side {{
      display: grid;
      gap: 20px;
    }}
    .panel {{
      padding: 18px;
    }}
    h1, h2 {{
      margin: 0 0 12px 0;
    }}
    .sub {{
      color: #5f6b76;
      line-height: 1.6;
    }}
    .form-grid {{
      display: grid;
      gap: 12px;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-weight: 700;
      font-size: 14px;
    }}
    select, input {{
      font: inherit;
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid #ced6df;
      background: #fff;
    }}
    button {{
      border: none;
      border-radius: 12px;
      padding: 12px 14px;
      font: inherit;
      font-weight: 800;
      color: white;
      background: #0f6f91;
      cursor: pointer;
    }}
    .secondary {{
      background: #edf2f7;
      color: #1f2937;
    }}
    .meta-row {{
      display: grid;
      gap: 6px;
      margin-bottom: 10px;
    }}
    code, pre {{
      font-family: "SFMono-Regular", Menlo, Monaco, monospace;
      font-size: 13px;
    }}
    code {{
      background: #f5f7fa;
      border-radius: 8px;
      padding: 4px 6px;
      word-break: break-all;
    }}
    .links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 10px;
    }}
    a {{
      color: #0f6f91;
      text-decoration: none;
      font-weight: 800;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: #fbfcfd;
      border: 1px solid #e3e8ef;
      border-radius: 14px;
      padding: 12px;
      min-height: 120px;
      line-height: 1.55;
    }}
    .dashboard-frame {{
      width: 100%;
      min-height: 1100px;
      border: 1px solid #d8dee6;
      border-radius: 18px;
      background: white;
    }}
    .checkbox {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
    }}
    .checkbox input {{
      width: auto;
      transform: scale(1.15);
    }}
    .status-bar {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 12px;
    }}
    .chip {{
      background: #eef6fa;
      color: #0e5f7c;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 13px;
      font-weight: 800;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>ZJU SEED Lab Studio</h1>
      <div class="sub">这个本地服务把 MASFactory 实验分支、现有 report packager、manual evidence UI 和最新 run 工件汇到一个端口里，适合直接演示和收尾。</div>
      <div class="status-bar">
        <span class="chip">workspace: {html.escape(str(runtime.workspace_root))}</span>
        <span class="chip">runs: {html.escape(str(RUNS_ROOT))}</span>
      </div>
    </section>
    <section class="layout">
      <div class="side">
        <section class="panel">
          <h2>启动一次 workflow</h2>
          <form id="run-form" class="form-grid">
            <label>workflow_mode
              <select name="workflow_mode">
                <option value="report_only" {"selected" if default_params["workflow_mode"] == "report_only" else ""}>report_only</option>
                <option value="package_review">package_review</option>
                <option value="full_lab">full_lab</option>
              </select>
            </label>
            <label>route_mode
              <select name="route_mode">
                <option value="reverse_ssh_direct" {"selected" if default_params["route_mode"] == "reverse_ssh_direct" else ""}>reverse_ssh_direct</option>
                <option value="seed_runner_session">seed_runner_session</option>
              </select>
            </label>
            <label>report_profile
              <input name="report_profile" value="{html.escape(default_params['report_profile'])}" />
            </label>
            <label>runner_profile
              <input name="runner_profile" value="{html.escape(default_params['runner_profile'])}" />
            </label>
            <label>graph_mode
              <select name="graph_mode">
                <option value="static" {"selected" if default_params["graph_mode"] == "static" else ""}>static</option>
                <option value="vibegraph">vibegraph</option>
              </select>
            </label>
            <label>ui_port
              <input name="ui_port" type="number" value="{default_params['ui_port']}" />
            </label>
            <label class="checkbox">
              <input name="launch_ui" type="checkbox" {"checked" if default_params["launch_ui"] else ""} />
              <span>运行后顺带拉起 manual UI</span>
            </label>
            <button type="submit">开始运行</button>
          </form>
          <div class="links">
            <button class="secondary" type="button" onclick="window.location.reload()">刷新页面</button>
          </div>
        </section>
        <section class="panel">
          <h2>最新工件</h2>
          {latest_rows or "<div class='sub'>当前还没有 latest run。</div>"}
          <div class="links">
            {"".join(quick_links) if quick_links else "<span class='sub'>暂无可打开链接。</span>"}
          </div>
        </section>
        <section class="panel">
          <h2>Manual UI</h2>
          <div class="meta-row"><span>status</span><code id="manual-ui-status">{html.escape(str(manual_ui_state.get("status") or "inactive"))}</code></div>
          <div class="meta-row"><span>url</span><code id="manual-ui-url">{html.escape(str(manual_ui_state.get("url") or ""))}</code></div>
          <div class="meta-row"><span>package_root</span><code id="manual-ui-package">{html.escape(str(manual_ui_state.get("package_root") or (latest.get("package_root") if latest else "")))}</code></div>
          <pre id="manual-ui-output">{html.escape(str(manual_ui_state.get("output") or "当前还没有单独拉起 manual UI。"))}</pre>
          <div class="links">
            <button type="button" onclick="startManualUi()">拉起最新 Package 的 Manual UI</button>
            {f"<a id='manual-ui-open' href='{html.escape(manual_ui_url)}' target='_blank'>打开当前 Manual UI</a>" if manual_ui_url else "<span id='manual-ui-open-wrap' class='sub'>拉起后这里会出现可点击地址。</span>"}
          </div>
        </section>
        {latest_job_block}
        <section class="panel">
          <h2>任务轮询</h2>
          <div class="sub" id="job-state-text">提交后这里会显示任务状态和输出尾部。</div>
          <pre id="job-tail">等待任务启动</pre>
        </section>
      </div>
      <section class="panel">
        <h2>最新 Dashboard</h2>
        {dashboard_iframe or "<div class='sub'>当前还没有 dashboard，先运行一次 workflow。</div>"}
        <div style="height:20px"></div>
        <h2>当前 Manual UI</h2>
        {manual_ui_iframe or "<div class='sub'>当前没有运行中的 manual UI，点击左侧按钮即可拉起。</div>"}
      </section>
    </section>
  </div>
  <script>
    let activeJobId = null;
    async function pollJob() {{
      if (!activeJobId) return;
      const resp = await fetch(`/api/job/${{activeJobId}}`);
      const data = await resp.json();
      document.getElementById('job-state-text').textContent = `job=${{data.job_id}} status=${{data.status}} returncode=${{data.returncode ?? ''}}`;
      document.getElementById('job-tail').textContent = data.tail || '暂无输出';
      if (data.status === 'completed' || data.status === 'failed') {{
        setTimeout(() => window.location.reload(), 800);
      }} else {{
        setTimeout(pollJob, 1200);
      }}
    }}
    async function startManualUi() {{
      const uiPort = Number(document.querySelector('input[name="ui_port"]').value || 8765);
      const resp = await fetch('/api/manual-ui/start', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ ui_port: uiPort }}),
      }});
      const data = await resp.json();
      document.getElementById('manual-ui-status').textContent = data.status || '';
      document.getElementById('manual-ui-url').textContent = data.url || '';
      document.getElementById('manual-ui-package').textContent = data.package_root || '';
      document.getElementById('manual-ui-output').textContent = data.output || 'manual UI 已启动';
      if (data.url) {{
        window.location.reload();
      }}
    }}
    document.getElementById('run-form').addEventListener('submit', async (event) => {{
      event.preventDefault();
      const form = event.target;
      const payload = Object.fromEntries(new FormData(form).entries());
      payload.launch_ui = form.launch_ui.checked;
      payload.ui_port = Number(payload.ui_port || 8765);
      const resp = await fetch('/api/run', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const data = await resp.json();
      activeJobId = data.job_id;
      document.getElementById('job-state-text').textContent = `job=${{data.job_id}} 已启动`;
      document.getElementById('job-tail').textContent = data.tail || '任务刚启动，等待输出...';
      setTimeout(pollJob, 1200);
    }});
  </script>
</body>
</html>"""


def serve(workspace_root: Path, preferred_port: int, open_browser: bool) -> tuple[ThreadingHTTPServer, str]:
    runtime = StudioRuntime(workspace_root)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body: bytes | str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
            payload = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            self._send(json.dumps(payload, ensure_ascii=False, indent=2), status=status, content_type="application/json; charset=utf-8")

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/":
                self._send(render_home(runtime))
                return
            if parsed.path == "/api/jobs":
                self._json({"jobs": runtime.list_jobs()})
                return
            if parsed.path.startswith("/api/job/"):
                job_id = parsed.path.rsplit("/", 1)[-1]
                job = runtime.get_job(job_id)
                if not job:
                    self._json({"error": "job not found"}, status=404)
                    return
                self._json(job.to_dict())
                return
            if parsed.path == "/api/latest":
                self._json({"latest": runtime.latest_run_summary()})
                return
            if parsed.path == "/api/manual-ui":
                self._json({"manual_ui": runtime.manual_ui_state()})
                return
            if parsed.path == "/file":
                query = urllib.parse.parse_qs(parsed.query)
                path_value = query.get("path", [""])[0]
                if not path_value:
                    self._send("missing path", status=400, content_type="text/plain; charset=utf-8")
                    return
                target = Path(path_value).resolve()
                allowed_roots = [runtime.workspace_root, RUNS_ROOT.resolve()]
                if not any(root == target or root in target.parents for root in allowed_roots):
                    self._send("forbidden", status=403, content_type="text/plain; charset=utf-8")
                    return
                if not target.exists() or not target.is_file():
                    self._send("not found", status=404, content_type="text/plain; charset=utf-8")
                    return
                self._send(target.read_bytes(), content_type=guess_content_type(target))
                return
            if parsed.path.startswith("/runs/"):
                relative = parsed.path[len("/runs/") :]
                target = (RUNS_ROOT / urllib.parse.unquote(relative)).resolve()
                if RUNS_ROOT.resolve() not in target.parents and target != RUNS_ROOT.resolve():
                    self._send("forbidden", status=403, content_type="text/plain; charset=utf-8")
                    return
                if not target.exists() or not target.is_file():
                    self._send("not found", status=404, content_type="text/plain; charset=utf-8")
                    return
                self._send(target.read_bytes(), content_type=guess_content_type(target))
                return
            self._send("not found", status=404, content_type="text/plain; charset=utf-8")

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path not in {"/api/run", "/api/manual-ui/start"}:
                self._send("not found", status=404, content_type="text/plain; charset=utf-8")
                return
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(content_length) if content_length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                self._json({"error": "invalid json"}, status=400)
                return
            if parsed.path == "/api/manual-ui/start":
                try:
                    state = runtime.start_manual_ui(preferred_port=int(payload.get("ui_port") or 8765))
                except Exception as exc:
                    self._json({"error": str(exc)}, status=500)
                    return
                self._json(state, status=202)
                return
            params = {
                "workflow_mode": str(payload.get("workflow_mode") or "report_only"),
                "route_mode": str(payload.get("route_mode") or "reverse_ssh_direct"),
                "report_profile": str(payload.get("report_profile") or "lab4-dns-combined"),
                "runner_profile": str(payload.get("runner_profile") or "lab4-dns-local"),
                "graph_mode": str(payload.get("graph_mode") or "static"),
                "ui_port": int(payload.get("ui_port") or 8765),
                "launch_ui": bool(payload.get("launch_ui")),
            }
            job = runtime.start_job(params)
            self._json(job.to_dict(), status=202)

        def log_message(self, format: str, *args: Any) -> None:
            return

    resolved_port = find_available_port("127.0.0.1", preferred_port)
    server = ThreadingHTTPServer(("127.0.0.1", resolved_port), Handler)
    url = f"http://127.0.0.1:{resolved_port}"
    print(f"ZJU SEED Lab Studio: {url}")
    if resolved_port != preferred_port:
        print(f"Preferred port {preferred_port} was unavailable. Switched to {resolved_port}.")
    if open_browser:
        webbrowser.open(url)
    return server, url


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local ZJU SEED Lab Studio demo surface.")
    parser.add_argument("--workspace-root", default=str(Path(__file__).resolve().parents[4]))
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument("--no-open-browser", action="store_true")
    args = parser.parse_args()
    server, _url = serve(Path(args.workspace_root), args.port, open_browser=not args.no_open_browser)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
