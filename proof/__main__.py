import argparse
import json
import sys
from pathlib import Path

from .core import ROOT, discover, preflight, run


def main():
    parser = argparse.ArgumentParser(description="Prove a local document workflow can run with network access denied.")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Start the local dashboard")
    serve.add_argument("--port", type=int, default=8741)
    sub.add_parser("discover", help="List local models and runtimes")
    for name in ["check", "run"]:
        p = sub.add_parser(name)
        p.add_argument("--model", default="")
        p.add_argument("--python", default=sys.executable)
        p.add_argument("--documents", default=str(ROOT / "data/fieldkit"))
        p.add_argument("--mode", choices=["mlx", "harness"], default="mlx")
        if name == "run":
            p.add_argument("--output", type=Path)
            p.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if args.command == "serve":
        from .server import serve
        serve(args.port)
        return 0
    if args.command == "discover":
        print(json.dumps(discover(), indent=2))
        return 0
    config = {k: getattr(args, k) for k in ["model", "python", "documents", "mode"]}
    if args.command == "check":
        checks = preflight(config)
        print(json.dumps(checks, indent=2))
        return 0 if all(c["passed"] for c in checks) else 1
    report = run(config, timeout=args.timeout)
    content = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content)
        args.output.chmod(0o600)
        print(f"{report['status']}: {args.output}")
    else:
        print(content)
    return 0 if report["status"] in {"verified", "harness_passed"} else 1


if __name__ == "__main__":
    sys.exit(main())
