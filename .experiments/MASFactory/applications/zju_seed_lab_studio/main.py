from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import webbrowser


_WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
_MASFACTORY_ROOT = Path(__file__).resolve().parents[2]
for path in (str(_WORKSPACE_ROOT), str(_MASFACTORY_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from masfactory import OpenAIModel, RootGraph, VibeGraph
from applications.zju_seed_lab_studio.artifacts import export_run_artifacts
from applications.zju_seed_lab_studio.workflow import build_seed_lab_studio_graph


def main():
    parser = argparse.ArgumentParser(description="ZJU SEED Lab Studio - MASFactory integration branch")
    parser.add_argument("--workspace-root", default=str(_WORKSPACE_ROOT))
    parser.add_argument("--workflow-mode", choices=["report_only", "package_review", "full_lab"], default="report_only")
    parser.add_argument("--route-mode", choices=["reverse_ssh_direct", "seed_runner_session"], default="reverse_ssh_direct")
    parser.add_argument("--report-profile", default="lab4-dns-combined")
    parser.add_argument("--runner-profile", default="lab4-dns-local")
    parser.add_argument("--launch-ui", action="store_true")
    parser.add_argument("--ui-port", type=int, default=8765)
    parser.add_argument("--graph-mode", choices=["static", "vibegraph"], default="static")
    parser.add_argument("--open-dashboard", action="store_true")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"))
    parser.add_argument("--api-key", default=os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL"))
    args = parser.parse_args()

    if args.graph_mode == "static":
        graph = build_seed_lab_studio_graph(
            workspace_root=args.workspace_root,
            workflow_mode=args.workflow_mode,
            route_mode=args.route_mode,
            report_profile=args.report_profile,
            runner_profile=args.runner_profile,
            launch_ui=args.launch_ui,
            ui_port=args.ui_port,
        )
    else:
        if not args.api_key:
            raise SystemExit("graph-mode=vibegraph requires OPENAI_API_KEY or --api-key")
        assets_dir = Path(__file__).resolve().parent / "assets"
        cache_dir = assets_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        build_instructions = (assets_dir / "build.txt").read_text(encoding="utf-8")
        model = OpenAIModel(
            model_name=args.model,
            api_key=args.api_key,
            base_url=args.base_url,
        )
        graph = RootGraph(name="zju_seed_lab_studio_vibegraph")
        vibe = graph.create_node(
            VibeGraph,
            name="studio_vibegraph",
            invoke_model=model,
            build_instructions=build_instructions,
            build_model=model,
            build_cache_path=str(cache_dir / "graph_design.json"),
        )
        graph.edge_from_entry(receiver=vibe, keys={})
        graph.edge_to_exit(sender=vibe, keys={})

    graph.build()
    output, _attrs = graph.invoke({})
    app_root = Path(__file__).resolve().parent
    summary = export_run_artifacts(
        graph=graph,
        output=output,
        app_root=app_root,
        workspace_root=Path(args.workspace_root).resolve(),
        graph_mode=args.graph_mode,
    )
    if args.open_dashboard:
        dashboard_path = Path(summary["artifacts"]["dashboard_html"]).resolve()
        webbrowser.open(dashboard_path.as_uri())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
