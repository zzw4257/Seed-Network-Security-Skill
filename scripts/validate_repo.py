#!/usr/bin/env python
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path) -> tuple[bool, str]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    output = (completed.stdout or completed.stderr).strip()
    return completed.returncode == 0, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate skills, scripts, and sample data in this repository.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    args = parser.parse_args()

    codex_home = Path(args.codex_home).expanduser().resolve()
    validator = codex_home / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"

    skills = [
        REPO_ROOT / "skills" / "zju-seed-lab-runner",
        REPO_ROOT / "skills" / "zju-seed-report-packager",
    ]

    if validator.exists():
        for skill in skills:
            ok, output = run(["python", str(validator), str(skill)], cwd=REPO_ROOT)
            print(f"[quick_validate] {skill.name}: {output}")
            if not ok:
                return 1
    else:
        print(f"[quick_validate] skipped: {validator} not found")

    compile_targets = [
        *sorted((REPO_ROOT / "skills" / "zju-seed-lab-runner" / "scripts").glob("*.py")),
        *sorted((REPO_ROOT / "skills" / "zju-seed-report-packager" / "scripts").glob("*.py")),
        *sorted((REPO_ROOT / ".experiments" / "MASFactory" / "applications" / "zju_seed_lab_studio").glob("*.py")),
    ]
    ok, output = run(["python", "-m", "py_compile", *[str(path) for path in compile_targets]], cwd=REPO_ROOT)
    print(f"[py_compile] {'ok' if ok else 'failed'}")
    if output:
        print(output)
    if not ok:
        return 1

    required_paths = [
        REPO_ROOT / "lab4-dns" / "DNS 攻击实验 - 本地攻击.md",
        REPO_ROOT / "lab4-dns" / "DNS 攻击实验 - 远程攻击.md",
        REPO_ROOT / "lab4-dns" / "Labsetup_DNS_Local ",
        REPO_ROOT / "lab4-dns" / "Labsetup_DNS_Remote",
        REPO_ROOT / "reports" / "lab4-dns-local" / "20260403-125920",
        REPO_ROOT / "reports" / "lab4-dns-remote" / "20260403-130805",
    ]
    for path in required_paths:
        if not path.exists():
            print(f"[missing] {path}", file=sys.stderr)
            return 1
    print("[sample-data] ok")

    inspect_cmd = [
        "python",
        str(REPO_ROOT / "skills" / "zju-seed-report-packager" / "scripts" / "report_packager.py"),
        "inspect",
        "--profile",
        "lab4-dns-combined",
        "--repo-root",
        str(REPO_ROOT),
    ]
    ok, output = run(inspect_cmd, cwd=REPO_ROOT)
    print(f"[report-packager inspect] {'ok' if ok else 'failed'}")
    if output:
        print(output)
    if not ok:
        return 1

    print("[done] repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
