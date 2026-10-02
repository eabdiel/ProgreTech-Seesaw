import argparse
import json
from pathlib import Path

from seesaw.backends import discover, research_plan
from seesaw.model import load_stl
from seesaw.pipeline import PipelineError, Settings, run_pipeline


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
    pipeline = sub.add_parser("validate-pipeline", help="Create a research-only Mono 4 candidate")
    pipeline.add_argument("model", type=Path)
    pipeline.add_argument("--job-dir", type=Path, required=True)
    pipeline.add_argument("--exposure-seconds", type=float, required=True)
    pipeline.add_argument("--bottom-exposure-seconds", type=float, required=True)
    pipeline.add_argument("--supports", action="store_true")
    pipeline.add_argument("--antialias", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            result = discover()
        elif args.command == "inspect":
            result = load_stl(args.model)[1].to_dict()
        elif args.command == "plan":
            result = {
                "status": "unqualified-research-only",
                "commands": research_plan(args.model, args.profile, args.work_dir),
            }
        else:
            result = run_pipeline(
                args.model,
                args.job_dir,
                Settings(
                    args.exposure_seconds,
                    args.bottom_exposure_seconds,
                    supports=args.supports,
                    antialias=args.antialias,
                ),
            )
    except (OSError, ValueError, PipelineError) as exc:
        parser.exit(2, f"Seesaw: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
