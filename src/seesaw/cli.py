import argparse
import json
from pathlib import Path

from seesaw.backends import discover, research_plan
from seesaw.model import load_stl


def main():
    parser = argparse.ArgumentParser(description="Seesaw foundation — no printer export yet")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Discover backend executables without running them")
    inspect = sub.add_parser("inspect", help="Inspect STL dimensions, topology and unrotated fit")
    inspect.add_argument("model", type=Path)
    plan = sub.add_parser("plan", help="Print an unqualified research plan; execute nothing")
    plan.add_argument("model", type=Path)
    plan.add_argument("--profile", type=Path, required=True)
    plan.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            result = discover()
        elif args.command == "inspect":
            result = load_stl(args.model)[1].to_dict()
        else:
            result = {
                "status": "unqualified-research-only",
                "commands": research_plan(args.model, args.profile, args.work_dir),
            }
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Seesaw: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
