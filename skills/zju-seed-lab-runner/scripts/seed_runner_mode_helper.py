#!/usr/bin/env python
import argparse
import textwrap


def build_env_block(args):
    lines = [
        f"SEED_RUNNER_LOCAL_HOST={args.local_host}",
        f"SEED_RUNNER_LOCAL_SSH_PORT={args.local_port}",
    ]
    if args.local_user:
        lines.append(f"SEED_RUNNER_LOCAL_USER={args.local_user}")
    if args.remote_to_local_key:
        lines.append(f"SEED_RUNNER_REMOTE_TO_LOCAL_KEY={args.remote_to_local_key}")
    lines.extend(
        [
            f"MACHINE_{args.machine_id}_HOST={args.remote_host}",
            f"MACHINE_{args.machine_id}_PORT={args.remote_port}",
            f"MACHINE_{args.machine_id}_USER={args.remote_user}",
            f"MACHINE_{args.machine_id}_KEY={args.remote_key}",
        ]
    )
    return "\n".join(lines)


def build_commands(args):
    workspace = args.workspace.rstrip("/")
    artifacts = f"{workspace}/artifacts"
    return textwrap.dedent(
        f"""\
        mkdir -p {workspace}
        cd {workspace}

        seed-runner mount create \\
          --machine {args.machine_id} \\
          --local-dir ./artifacts

        seed-runner session create \\
          --machine {args.machine_id} \\
          --mount-id <mount-id> \\
          --name {args.session_name}

        seed-runner session exec \\
          --session <session-id> \\
          --cmd "<command>"

        seed-runner session status --session <session-id>

        seed-runner session destroy --session <session-id>
        seed-runner mount destroy --mount-id <mount-id>
        """
    ).strip()


def main():
    parser = argparse.ArgumentParser(description="Render a concrete seed-runner backup-route template.")
    parser.add_argument("--machine-id", default="vm-seed-01")
    parser.add_argument("--remote-host", required=True)
    parser.add_argument("--remote-port", default="22")
    parser.add_argument("--remote-user", required=True)
    parser.add_argument("--remote-key", required=True)
    parser.add_argument("--local-host", required=True)
    parser.add_argument("--local-port", default="22")
    parser.add_argument("--local-user")
    parser.add_argument("--remote-to-local-key")
    parser.add_argument("--workspace", default="runs/seed-exp-01")
    parser.add_argument("--session-name", default="seed-exp-01")
    args = parser.parse_args()

    print("# .env.machines")
    print(build_env_block(args))
    print()
    print("# standard seed-runner command chain")
    print(build_commands(args))


if __name__ == "__main__":
    main()
