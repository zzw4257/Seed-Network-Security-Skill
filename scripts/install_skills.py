#!/usr/bin/env python
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"


def discover_skills() -> list[str]:
    skills = []
    for path in sorted(SKILLS_ROOT.iterdir()):
        if path.is_dir() and (path / "SKILL.md").exists():
            skills.append(path.name)
    return skills


def copy_skill(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
    )


def run_quick_validate(skill_path: Path, codex_home: Path) -> tuple[bool, str]:
    validator = codex_home / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    if not validator.exists():
        return True, f"跳过 quick_validate：未找到 {validator}"
    completed = subprocess.run(
        ["python", str(validator), str(skill_path)],
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or completed.stderr).strip()
    return completed.returncode == 0, output


def main() -> int:
    parser = argparse.ArgumentParser(description="Install repository skills into ~/.codex/skills.")
    parser.add_argument("--skill", action="append", dest="skills", help="Install only the named skill. Repeatable.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex"))
    parser.add_argument("--validate", action="store_true", help="Run quick_validate before and after install when available.")
    parser.add_argument("--list", action="store_true", help="List installable skills and exit.")
    args = parser.parse_args()

    available = discover_skills()
    if args.list:
        print("\n".join(available))
        return 0

    selected = args.skills or available
    missing = [name for name in selected if name not in available]
    if missing:
        print(f"未知 skill: {', '.join(missing)}", file=sys.stderr)
        return 1

    codex_home = Path(args.codex_home).expanduser().resolve()
    target_root = codex_home / "skills"
    target_root.mkdir(parents=True, exist_ok=True)

    for name in selected:
        src = SKILLS_ROOT / name
        dst = target_root / name
        print(f"[install] {name}")
        if args.validate:
            ok, output = run_quick_validate(src, codex_home)
            print(f"[validate:source] {name}: {output}")
            if not ok:
                return 1
        copy_skill(src, dst)
        print(f"[copied] {src} -> {dst}")
        if args.validate:
            ok, output = run_quick_validate(dst, codex_home)
            print(f"[validate:installed] {name}: {output}")
            if not ok:
                return 1

    print("[done] skills installed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
