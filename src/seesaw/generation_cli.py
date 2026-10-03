"""Explicit image-to-mesh tool for local agents and headless workflows."""

import argparse
import json
import secrets
from pathlib import Path

from seesaw.generation import ReliefSettings, create_relief


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Fresh job directory")
    parser.add_argument("--mode", choices=("relief", "trellis"), default="relief")
    parser.add_argument("--width-mm", type=float, default=60)
    parser.add_argument("--base-mm", type=float, default=2)
    parser.add_argument("--depth-mm", type=float, default=3)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--repair", action="store_true", help="May alter fine details")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--weights", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "relief":
            args.output.mkdir(parents=True, exist_ok=False)
            output = args.output / "relief.stl"
            result = create_relief(
                args.image,
                output,
                ReliefSettings(args.width_mm, args.base_mm, args.depth_mm, args.invert),
            )
        else:
            from seesaw.trellis import generate

            config_path = Path.home() / ".config/progretech-seesaw/generation.json"
            config = json.loads(config_path.read_text()) if config_path.is_file() else {}
            binary = args.binary or Path(config.get("binary", ""))
            weights = args.weights or Path(config.get("weights", ""))
            output = generate(
                binary,
                weights,
                args.image,
                args.output,
                width_mm=args.width_mm,
                seed=args.seed if args.seed is not None else secrets.randbelow(2**31),
                repair=args.repair,
            )
            result = json.loads(output.with_suffix(".json").read_text())
        print(
            json.dumps(
                {
                    "ok": True,
                    "artifact": str(output.resolve()),
                    "mode": args.mode,
                    "validation": result,
                    "physical_print_qualified": False,
                }
            )
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "fallback": "explicit CPU relief"}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
