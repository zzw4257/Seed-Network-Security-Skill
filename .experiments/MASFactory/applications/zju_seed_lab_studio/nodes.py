from __future__ import annotations

import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> dict[str, object]:
    completed = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _clean_output(text: str, max_lines: int = 12) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["..."]
    return "\n".join(lines)


def _package_pdf(package_root: Path) -> str:
    if not package_root.exists():
        return ""
    pdfs = sorted(package_root.glob("*.pdf"))
    return str(pdfs[0]) if pdfs else ""


def _read_startup_lines_from_file(log_path: Path, *, max_lines: int = 4, timeout_s: float = 2.0) -> list[str]:
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


def _passthrough(input: dict, keys: list[str]) -> dict[str, object]:
    return {key: input[key] for key in keys if key in input}


def context_summary_forward(input: dict, attributes: dict) -> dict[str, object]:
    workspace_root = Path(attributes["workspace_root"]).resolve()
    summary = {
        "workspace_root": str(workspace_root),
        "workflow_mode": attributes["workflow_mode"],
        "route_mode": attributes["route_mode"],
        "report_profile": attributes["report_profile"],
        "runner_profile": attributes["runner_profile"],
    }
    return {
        "workspace_root": str(workspace_root),
        "workflow_mode": attributes["workflow_mode"],
        "route_mode": attributes["route_mode"],
        "report_profile": attributes["report_profile"],
        "runner_profile": attributes["runner_profile"],
        "context_summary": json.dumps(summary, ensure_ascii=False, indent=2),
    }


def route_summary_forward(input: dict, attributes: dict) -> dict[str, object]:
    route_mode = attributes["route_mode"]
    if route_mode == "reverse_ssh_direct":
        route_summary = (
            "Current route: reverse-SSH direct mode. This is the existing mainline for the current "
            "workspace, suitable for a single prepared teaching VM with the reverse tunnel already available. "
            "It stays closest to the already-validated Proxmox + reverse SSH + Docker workflow."
        )
    else:
        route_summary = (
            "Current route: seed-runner session mode. This is the generalized backup route based on "
            "sshfs + tmux + session exec, intended for richer multi-machine orchestration. "
            "It is better suited to future multi-machine scaling and richer session visualization."
        )
    return {"route_summary": route_summary}


def runner_preflight_forward(input: dict, attributes: dict) -> dict[str, object]:
    workspace_root = Path(attributes["workspace_root"]).resolve()
    runner_script = workspace_root / "skills" / "zju-seed-lab-runner" / "scripts" / "seed_lab_runner.py"
    if attributes["workflow_mode"] != "full_lab":
        return {
            **_passthrough(input, ["route_summary"]),
            "runner_preflight_status": "skipped",
            "runner_preflight_output": "Skipped because workflow_mode is not full_lab.",
            "runner_preflight_command": "",
        }
    result = _run(
        [
            "python",
            str(runner_script),
            "preflight",
            "--profile",
            attributes["runner_profile"],
            "--repo-root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )
    return {
        **_passthrough(input, ["route_summary"]),
        "runner_preflight_status": "ok" if result["returncode"] == 0 else "failed",
        "runner_preflight_output": _clean_output(result["stdout"] or result["stderr"]),
        "runner_preflight_command": result["command"],
    }


def runner_execute_forward(input: dict, attributes: dict) -> dict[str, object]:
    workspace_root = Path(attributes["workspace_root"]).resolve()
    runner_script = workspace_root / "skills" / "zju-seed-lab-runner" / "scripts" / "seed_lab_runner.py"
    if attributes["workflow_mode"] != "full_lab":
        return {
            **_passthrough(input, ["route_summary", "runner_preflight_status", "runner_preflight_output", "runner_preflight_command"]),
            "runner_execute_status": "skipped",
            "runner_execute_output": "Skipped because workflow_mode is not full_lab.",
            "runner_execute_command": "",
        }
    result = _run(
        [
            "python",
            str(runner_script),
            "full-run",
            "--profile",
            attributes["runner_profile"],
            "--repo-root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )
    return {
        **_passthrough(input, ["route_summary", "runner_preflight_status", "runner_preflight_output", "runner_preflight_command"]),
        "runner_execute_status": "ok" if result["returncode"] == 0 else "failed",
        "runner_execute_output": _clean_output(result["stdout"] or result["stderr"], max_lines=18),
        "runner_execute_command": result["command"],
    }


def report_package_forward(input: dict, attributes: dict) -> dict[str, object]:
    workspace_root = Path(attributes["workspace_root"]).resolve()
    report_script = workspace_root / "skills" / "zju-seed-report-packager" / "scripts" / "report_packager.py"
    package_root = workspace_root / "report-packages" / attributes["report_profile"]
    mode = attributes["workflow_mode"]
    passthrough = _passthrough(
        input,
        [
            "route_summary",
            "runner_preflight_status",
            "runner_preflight_output",
            "runner_preflight_command",
            "runner_execute_status",
            "runner_execute_output",
            "runner_execute_command",
        ],
    )
    inspect_cmd = [
        "python",
        str(report_script),
        "inspect",
        "--profile",
        attributes["report_profile"],
        "--repo-root",
        str(workspace_root),
    ]
    build_cmd = [
        "python",
        str(report_script),
        "build",
        "--profile",
        attributes["report_profile"],
        "--repo-root",
        str(workspace_root),
    ]
    if mode == "report_only":
        result = _run(inspect_cmd, cwd=workspace_root)
        status = "ok" if result["returncode"] == 0 else "failed"
        return {
            **passthrough,
            "report_stage_status": status,
            "report_stage_output": _clean_output(result["stdout"] or result["stderr"], max_lines=18),
            "report_stage_command": result["command"],
            "report_stage_inspect_command": result["command"],
            "report_stage_build_command": "",
            "package_root": str(package_root),
            "package_pdf": _package_pdf(package_root),
        }
    inspect_result = _run(inspect_cmd, cwd=workspace_root) if mode == "package_review" else None
    build_result = _run(build_cmd, cwd=workspace_root)
    inspect_status = "ok" if not inspect_result or inspect_result["returncode"] == 0 else "failed"
    build_status = "ok" if build_result["returncode"] == 0 else "failed"
    status = "ok" if inspect_status == "ok" and build_status == "ok" else "failed"
    combined_output_parts = []
    if inspect_result:
        combined_output_parts.append("Inspect:\n" + _clean_output(inspect_result["stdout"] or inspect_result["stderr"], max_lines=18))
    combined_output_parts.append("Build:\n" + _clean_output(build_result["stdout"] or build_result["stderr"], max_lines=18))
    return {
        **passthrough,
        "report_stage_status": status,
        "report_stage_output": "\n\n".join(combined_output_parts),
        "report_stage_command": build_result["command"],
        "report_stage_inspect_command": inspect_result["command"] if inspect_result else "",
        "report_stage_build_command": build_result["command"],
        "package_root": str(package_root),
        "package_pdf": _package_pdf(package_root),
    }


def manual_ui_forward(input: dict, attributes: dict) -> dict[str, object]:
    workspace_root = Path(attributes["workspace_root"]).resolve()
    package_root = Path(input.get("package_root") or (workspace_root / "report-packages" / attributes["report_profile"])).resolve()
    ui_script = workspace_root / "skills" / "zju-seed-report-packager" / "scripts" / "manual_evidence_ui.py"
    command = f"python -u {ui_script} --package-root {package_root} --repo-root {workspace_root} --port {attributes['ui_port']}"
    passthrough = _passthrough(
        input,
        [
            "route_summary",
            "runner_preflight_status",
            "runner_preflight_output",
            "runner_preflight_command",
            "runner_execute_status",
            "runner_execute_output",
            "runner_execute_command",
            "report_stage_status",
            "report_stage_output",
            "report_stage_command",
            "report_stage_inspect_command",
            "report_stage_build_command",
            "package_pdf",
        ],
    )
    if not attributes.get("launch_ui", False):
        return {
            **passthrough,
            "package_root": str(package_root),
            "manual_ui_status": "skipped",
            "manual_ui_output": "UI launch skipped by configuration.",
            "manual_ui_command": command,
            "manual_ui_pid": "",
            "manual_ui_url": "",
            "manual_ui_port": "",
            "manual_ui_log": "",
        }
    app_runs_dir = Path(__file__).resolve().parent / "runs" / "_ui_logs"
    app_runs_dir.mkdir(parents=True, exist_ok=True)
    log_path = app_runs_dir / f"manual-ui-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [
                "python",
                "-u",
                str(ui_script),
                "--package-root",
                str(package_root),
                "--repo-root",
                str(workspace_root),
                "--port",
                str(attributes["ui_port"]),
                "--no-open-browser",
            ],
            cwd=workspace_root,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    startup_lines = _read_startup_lines_from_file(log_path)
    startup_text = "\n".join(startup_lines) if startup_lines else "UI process started."
    url = ""
    port = ""
    for line in startup_lines:
        match = re.search(r"Manual evidence UI:\s*(http://[^\s]+)", line)
        if match:
            url = match.group(1)
            port = url.rsplit(":", 1)[-1]
            break
    return {
        **passthrough,
        "package_root": str(package_root),
        "manual_ui_status": "launched",
        "manual_ui_output": startup_text,
        "manual_ui_pid": process.pid,
        "manual_ui_package_root": str(package_root),
        "manual_ui_command": command,
        "manual_ui_url": url,
        "manual_ui_port": port,
        "manual_ui_log": str(log_path),
    }


def verify_forward(input: dict, attributes: dict) -> dict[str, object]:
    workspace_root = Path(attributes["workspace_root"]).resolve()
    report_script = workspace_root / "skills" / "zju-seed-report-packager" / "scripts" / "report_packager.py"
    package_root = workspace_root / "report-packages" / attributes["report_profile"]
    passthrough = {
        "package_root": str(package_root),
        "manual_ui_status": input.get("manual_ui_status", ""),
        "manual_ui_output": input.get("manual_ui_output", ""),
        "manual_ui_command": input.get("manual_ui_command", ""),
        "manual_ui_pid": input.get("manual_ui_pid", ""),
        "manual_ui_url": input.get("manual_ui_url", ""),
        "manual_ui_port": input.get("manual_ui_port", ""),
        "manual_ui_log": input.get("manual_ui_log", ""),
        "route_summary": input.get("route_summary", ""),
        "runner_preflight_status": input.get("runner_preflight_status", ""),
        "runner_preflight_output": input.get("runner_preflight_output", ""),
        "runner_preflight_command": input.get("runner_preflight_command", ""),
        "runner_execute_status": input.get("runner_execute_status", ""),
        "runner_execute_output": input.get("runner_execute_output", ""),
        "runner_execute_command": input.get("runner_execute_command", ""),
        "report_stage_status": input.get("report_stage_status", ""),
        "report_stage_output": input.get("report_stage_output", ""),
        "report_stage_command": input.get("report_stage_command", ""),
        "report_stage_inspect_command": input.get("report_stage_inspect_command", ""),
        "report_stage_build_command": input.get("report_stage_build_command", ""),
        "package_pdf": input.get("package_pdf", ""),
    }
    if attributes["workflow_mode"] == "report_only":
        return {
            **passthrough,
            "verify_status": "skipped",
            "verify_output": "Skipped in report_only mode.",
            "verify_command": "",
            "verification_dir": str(package_root / "evidence" / "auto" / "verification"),
        }
    verify_cmd = [
        "python",
        str(report_script),
        "verify-evidence",
        "--profile",
        attributes["report_profile"],
        "--repo-root",
        str(workspace_root),
    ]
    result = _run(verify_cmd, cwd=workspace_root)
    return {
        **passthrough,
        "verify_status": "ok" if result["returncode"] == 0 else "failed",
        "verify_output": _clean_output(result["stdout"] or result["stderr"], max_lines=18),
        "verify_command": result["command"],
        "verification_dir": str(package_root / "evidence" / "auto" / "verification"),
    }


def summary_forward(input: dict, attributes: dict) -> dict[str, object]:
    package_root = input.get("package_root") or str(Path(attributes["workspace_root"]).resolve() / "report-packages" / attributes["report_profile"])
    package_pdf = input.get("package_pdf") or _package_pdf(Path(package_root))
    payload = {
        "workflow_mode": attributes["workflow_mode"],
        "route_mode": attributes["route_mode"],
        "report_profile": attributes["report_profile"],
        "runner_profile": attributes["runner_profile"],
        "package_root": package_root,
        "package_pdf": package_pdf,
        "route_summary": input.get("route_summary", ""),
        "manual_ui_status": input.get("manual_ui_status"),
        "manual_ui_output": input.get("manual_ui_output"),
        "manual_ui_command": input.get("manual_ui_command"),
        "manual_ui_pid": input.get("manual_ui_pid"),
        "manual_ui_url": input.get("manual_ui_url"),
        "manual_ui_port": input.get("manual_ui_port"),
        "manual_ui_log": input.get("manual_ui_log"),
        "verify_status": input.get("verify_status"),
        "verify_output": input.get("verify_output"),
        "verification_dir": input.get("verification_dir"),
        "stages": {
            "runner_preflight": {
                "status": input.get("runner_preflight_status"),
                "command": input.get("runner_preflight_command"),
                "output": input.get("runner_preflight_output"),
            },
            "runner_execute": {
                "status": input.get("runner_execute_status"),
                "command": input.get("runner_execute_command"),
                "output": input.get("runner_execute_output"),
            },
            "report_package": {
                "status": input.get("report_stage_status"),
                "command": input.get("report_stage_command"),
                "inspect_command": input.get("report_stage_inspect_command"),
                "build_command": input.get("report_stage_build_command"),
                "output": input.get("report_stage_output"),
                "pdf": package_pdf,
            },
            "manual_ui": {
                "status": input.get("manual_ui_status"),
                "command": input.get("manual_ui_command"),
                "output": input.get("manual_ui_output"),
                "pid": input.get("manual_ui_pid"),
                "url": input.get("manual_ui_url"),
                "log": input.get("manual_ui_log"),
            },
            "verify": {
                "status": input.get("verify_status"),
                "command": input.get("verify_command"),
                "output": input.get("verify_output"),
                "verification_dir": input.get("verification_dir"),
            },
        },
    }
    return {
        "studio_summary_path": "",
        "studio_summary_data": payload,
        "studio_summary": json.dumps(payload, ensure_ascii=False, indent=2),
    }
