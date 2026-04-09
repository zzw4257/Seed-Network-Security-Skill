#!/usr/bin/env python
import argparse
import html
import json
import socket
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def content_type_for(path):
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def find_available_port(host, preferred_port, search_limit=40):
    for port in range(preferred_port, preferred_port + search_limit):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"无法在 {preferred_port}-{preferred_port + search_limit - 1} 范围内找到可用端口")


class ManualEvidenceUI:
    def __init__(self, package_root, repo_root):
        self.package_root = Path(package_root).resolve()
        self.repo_root = Path(repo_root).resolve()
        self.context = load_json(self.package_root / "report-context.json")
        self.manual_dir = self.package_root / "evidence" / "manual"
        self.manual_dir.mkdir(parents=True, exist_ok=True)
        self.auto_board_dir = self.package_root / self.context["auto_terminal_boards_dir"]
        self.metadata_path = self.manual_dir / "manual-inputs.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self):
        if self.metadata_path.exists():
            try:
                return load_json(self.metadata_path)
            except Exception:
                return {"notes": "", "values": {}}
        return {"notes": "", "values": {}}

    def save_metadata(self, notes, raw_values):
        values = {}
        raw_values = raw_values.strip()
        if raw_values:
            values = json.loads(raw_values)
        payload = {"notes": notes.strip(), "values": values}
        self.metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.metadata = payload

    def slot_rows(self):
        rows = []
        for slot in self.context["screenshot_slots"]:
            manual_path = self.manual_dir / slot["filename"]
            auto_path = self.auto_board_dir / slot["filename"]
            rows.append(
                {
                    "slot": slot,
                    "manual_exists": manual_path.exists(),
                    "manual_path": manual_path,
                    "auto_exists": auto_path.exists(),
                    "auto_path": auto_path,
                }
            )
        return rows

    def build_page(self, message=""):
        cards = []
        for row in self.slot_rows():
            slot = row["slot"]
            preview_src = f"/file?kind=manual&name={urllib.parse.quote(slot['filename'])}" if row["manual_exists"] else f"/file?kind=auto&name={urllib.parse.quote(slot['filename'])}"
            status = "已放入手工图" if row["manual_exists"] else "当前使用自动图"
            cards.append(
                f"""
                <section class="card">
                  <div class="card-head">
                    <div>
                      <div class="slot-name">{html.escape(slot['filename'])}</div>
                      <div class="slot-meta">{html.escape(slot['section'])} | {html.escape(status)}</div>
                    </div>
                  </div>
                  <img class="preview" src="{preview_src}" />
                  <div class="slot-desc">{html.escape(slot['description'])}</div>
                  <form method="post" action="/upload" enctype="multipart/form-data" class="upload-form">
                    <input type="hidden" name="slot" value="{html.escape(slot['filename'])}" />
                    <input type="file" name="image" accept=".png,.jpg,.jpeg,.webp" required />
                    <button type="submit">上传并替换为这张图</button>
                  </form>
                </section>
                """
            )
        notes = html.escape(self.metadata.get("notes", ""))
        values = html.escape(json.dumps(self.metadata.get("values", {}), indent=2, ensure_ascii=False))
        banner = f"<div class='banner'>{html.escape(message)}</div>" if message else ""
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>lab4-dns 手工图管理</title>
  <style>
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
      background: #f5f6f8;
      color: #202124;
    }}
    .wrap {{
      max-width: 1500px;
      margin: 0 auto;
      padding: 20px 24px 40px 24px;
    }}
    h1 {{ margin: 0 0 8px 0; }}
    .sub {{ color: #666; margin-bottom: 16px; }}
    .banner {{
      background: #e7f4ea;
      color: #166534;
      border: 1px solid #b7e4c7;
      padding: 10px 12px;
      border-radius: 10px;
      margin-bottom: 16px;
    }}
    .controls {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 18px;
    }}
    .panel {{
      background: white;
      border: 1px solid #d9dde3;
      border-radius: 14px;
      padding: 16px;
    }}
    textarea {{
      width: 100%;
      min-height: 150px;
      font: 14px/1.5 Menlo, Monaco, monospace;
      border: 1px solid #cfd3da;
      border-radius: 10px;
      padding: 10px;
      box-sizing: border-box;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .card {{
      background: white;
      border: 1px solid #d9dde3;
      border-radius: 14px;
      padding: 14px;
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }}
    .slot-name {{
      font-weight: 800;
      font-size: 15px;
      word-break: break-all;
    }}
    .slot-meta {{
      color: #666;
      font-size: 13px;
      margin-top: 4px;
    }}
    .preview {{
      width: 100%;
      border: 1px solid #e3e5e8;
      border-radius: 10px;
      background: #fafafa;
      margin-bottom: 10px;
    }}
    .slot-desc {{
      font-size: 14px;
      line-height: 1.5;
      margin-bottom: 10px;
    }}
    .upload-form {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}
    button {{
      background: #0f81a8;
      color: white;
      border: none;
      border-radius: 10px;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
    }}
    .actions {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 10px;
    }}
    .minor {{
      background: #edf2f7;
      color: #1f2937;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>lab4-dns 手工图与补充信息面板</h1>
    <div class="sub">上传图片时不用改名，系统会按槽位自动落到正确文件名；保存额外说明后可一键重编 PDF。</div>
    {banner}
    <div class="controls">
      <section class="panel">
        <h2>补充说明</h2>
        <form method="post" action="/save-text">
          <textarea name="notes" placeholder="写给报告生成器的补充说明，例如某张图为什么这样取景。">{notes}</textarea>
          <div class="actions">
            <button type="submit">保存说明</button>
          </div>
        </form>
      </section>
      <section class="panel">
        <h2>补充数值 / 选项</h2>
        <form method="post" action="/save-values">
          <textarea name="values" placeholder='{{"bridge": "br-xxxx", "attacker_id": "15"}}'>{values}</textarea>
          <div class="actions">
            <button type="submit">保存 JSON</button>
            <form method="post" action="/rebuild">
              <button class="minor" type="submit">重编 PDF</button>
            </form>
          </div>
        </form>
      </section>
    </div>
    <div class="grid">
      {''.join(cards)}
    </div>
  </div>
</body>
</html>"""


def serve_ui(package_root, repo_root, port, open_browser=False):
    ui = ManualEvidenceUI(package_root, repo_root)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, content_type="text/html; charset=utf-8", status=200):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/":
                self._send(ui.build_page())
                return
            if parsed.path == "/file":
                params = urllib.parse.parse_qs(parsed.query)
                kind = params.get("kind", [""])[0]
                name = params.get("name", [""])[0]
                path = None
                if kind == "manual":
                    path = ui.manual_dir / name
                elif kind == "auto":
                    path = ui.auto_board_dir / name
                if path and path.exists():
                    self._send(path.read_bytes(), content_type=content_type_for(path))
                    return
                self._send("not found", status=404)
                return
            self._send("not found", status=404)

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length)
            content_type = self.headers.get("Content-Type", "")

            if parsed.path in {"/save-text", "/save-values"}:
                data = urllib.parse.parse_qs(body.decode("utf-8"))
                notes = data.get("notes", [""])[0] if parsed.path == "/save-text" else ui.metadata.get("notes", "")
                values = data.get("values", [""])[0] if parsed.path == "/save-values" else json.dumps(ui.metadata.get("values", {}), ensure_ascii=False)
                try:
                    ui.save_metadata(notes, values)
                    self._send(ui.build_page("已保存补充信息。"))
                except Exception as exc:
                    self._send(ui.build_page(f"保存失败：{exc}"))
                return

            if parsed.path == "/rebuild":
                script = ui.repo_root / "skills" / "zju-seed-report-packager" / "scripts" / "report_packager.py"
                cmd = [
                    "python",
                    str(script),
                    "compile",
                    "--package-root",
                    str(ui.package_root),
                    "--profile",
                    ui.context["profile_id"],
                    "--repo-root",
                    str(ui.repo_root),
                ]
                completed = subprocess.run(cmd, cwd=ui.repo_root, capture_output=True, text=True)
                message = "PDF 已重编完成。" if completed.returncode == 0 else f"重编失败：{completed.stderr or completed.stdout}"
                self._send(ui.build_page(message))
                return

            if parsed.path == "/upload":
                boundary_match = re.search(r"boundary=(.*)", content_type)
                if not boundary_match:
                    self._send(ui.build_page("上传失败：缺少 multipart boundary"))
                    return
                boundary = boundary_match.group(1).encode("utf-8")
                parts = body.split(b"--" + boundary)
                slot_name = None
                file_bytes = None
                filename = None
                for part in parts:
                    if b"Content-Disposition" not in part:
                        continue
                    headers, _, payload = part.partition(b"\r\n\r\n")
                    disposition = headers.decode("utf-8", errors="ignore")
                    payload = payload.rstrip(b"\r\n-")
                    if 'name="slot"' in disposition:
                        slot_name = payload.decode("utf-8", errors="ignore")
                    elif 'name="image"' in disposition:
                        filename_match = re.search(r'filename="([^"]+)"', disposition)
                        filename = filename_match.group(1) if filename_match else "upload.png"
                        file_bytes = payload
                if slot_name and file_bytes:
                    target = ui.manual_dir / slot_name
                    target.write_bytes(file_bytes)
                    self._send(ui.build_page(f"已更新 {slot_name}（源文件：{filename}）。"))
                    return
                self._send(ui.build_page("上传失败：没有解析到图片或槽位名称。"))
                return

            self._send("not found", status=404)

    resolved_port = find_available_port("127.0.0.1", port)
    server = ThreadingHTTPServer(("127.0.0.1", resolved_port), Handler)
    url = f"http://127.0.0.1:{resolved_port}"
    print(f"Manual evidence UI: {url}")
    if resolved_port != port:
        print(f"Preferred port {port} was unavailable. Switched to {resolved_port}.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Serve a local manual evidence UI for report packages.")
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open-browser", action="store_true")
    args = parser.parse_args()
    serve_ui(args.package_root, args.repo_root, args.port, open_browser=not args.no_open_browser)


if __name__ == "__main__":
    main()
