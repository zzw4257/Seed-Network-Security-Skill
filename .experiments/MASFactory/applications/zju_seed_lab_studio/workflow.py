from __future__ import annotations

from masfactory import CustomNode, RootGraph

from applications.zju_seed_lab_studio.nodes import (
    context_summary_forward,
    manual_ui_forward,
    report_package_forward,
    route_summary_forward,
    runner_execute_forward,
    runner_preflight_forward,
    summary_forward,
    verify_forward,
)


def build_seed_lab_studio_graph(*, workspace_root: str, workflow_mode: str, route_mode: str, report_profile: str, runner_profile: str, launch_ui: bool, ui_port: int) -> RootGraph:
    graph = RootGraph(
        name="zju_seed_lab_studio",
        attributes={
            "workspace_root": workspace_root,
            "workflow_mode": workflow_mode,
            "route_mode": route_mode,
            "report_profile": report_profile,
            "runner_profile": runner_profile,
            "launch_ui": launch_ui,
            "ui_port": ui_port,
        },
    )

    context_summary = graph.create_node(CustomNode, "context_summary", forward=context_summary_forward)
    route_summary = graph.create_node(CustomNode, "route_summary", forward=route_summary_forward)
    runner_preflight = graph.create_node(CustomNode, "runner_preflight", forward=runner_preflight_forward)
    runner_execute = graph.create_node(CustomNode, "runner_execute", forward=runner_execute_forward)
    report_package = graph.create_node(CustomNode, "report_package", forward=report_package_forward)
    manual_ui = graph.create_node(CustomNode, "manual_ui", forward=manual_ui_forward)
    verify = graph.create_node(CustomNode, "verify", forward=verify_forward)
    summary = graph.create_node(CustomNode, "summary", forward=summary_forward)

    graph.edge_from_entry(receiver=context_summary, keys={})
    graph.create_edge(sender=context_summary, receiver=route_summary, keys={})
    graph.create_edge(sender=route_summary, receiver=runner_preflight, keys={"route_summary": ""})
    graph.create_edge(
        sender=runner_preflight,
        receiver=runner_execute,
        keys={
            "route_summary": "",
            "runner_preflight_status": "",
            "runner_preflight_output": "",
            "runner_preflight_command": "",
        },
    )
    graph.create_edge(
        sender=runner_execute,
        receiver=report_package,
        keys={
            "route_summary": "",
            "runner_preflight_status": "",
            "runner_preflight_output": "",
            "runner_preflight_command": "",
            "runner_execute_status": "",
            "runner_execute_output": "",
            "runner_execute_command": "",
        },
    )
    graph.create_edge(
        sender=report_package,
        receiver=manual_ui,
        keys={
            "route_summary": "",
            "runner_preflight_status": "",
            "runner_preflight_output": "",
            "runner_preflight_command": "",
            "runner_execute_status": "",
            "runner_execute_output": "",
            "runner_execute_command": "",
            "package_root": "",
            "package_pdf": "",
            "report_stage_status": "",
            "report_stage_output": "",
            "report_stage_command": "",
            "report_stage_inspect_command": "",
            "report_stage_build_command": "",
        },
    )
    graph.create_edge(
        sender=manual_ui,
        receiver=verify,
        keys={
            "route_summary": "",
            "runner_preflight_status": "",
            "runner_preflight_output": "",
            "runner_preflight_command": "",
            "runner_execute_status": "",
            "runner_execute_output": "",
            "runner_execute_command": "",
            "package_root": "",
            "package_pdf": "",
            "report_stage_status": "",
            "report_stage_output": "",
            "report_stage_command": "",
            "report_stage_inspect_command": "",
            "report_stage_build_command": "",
            "manual_ui_status": "",
            "manual_ui_output": "",
            "manual_ui_command": "",
            "manual_ui_pid": "",
            "manual_ui_url": "",
            "manual_ui_port": "",
            "manual_ui_log": "",
        },
    )
    graph.create_edge(
        sender=verify,
        receiver=summary,
        keys={
            "route_summary": "",
            "runner_preflight_status": "",
            "runner_preflight_output": "",
            "runner_preflight_command": "",
            "runner_execute_status": "",
            "runner_execute_output": "",
            "runner_execute_command": "",
            "package_root": "",
            "package_pdf": "",
            "report_stage_status": "",
            "report_stage_output": "",
            "report_stage_command": "",
            "report_stage_inspect_command": "",
            "report_stage_build_command": "",
            "manual_ui_status": "",
            "manual_ui_output": "",
            "manual_ui_command": "",
            "manual_ui_pid": "",
            "manual_ui_url": "",
            "manual_ui_port": "",
            "manual_ui_log": "",
            "verify_status": "",
            "verify_output": "",
            "verify_command": "",
            "verification_dir": "",
        },
    )
    graph.edge_to_exit(
        sender=summary,
        keys={
            "studio_summary_path": "",
            "studio_summary": "",
        },
    )

    return graph
