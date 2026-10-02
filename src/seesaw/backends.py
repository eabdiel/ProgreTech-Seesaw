"""Backend discovery and research command plans, never an implicit print/export API."""

import shutil
from pathlib import Path


def discover() -> dict:
    return {
        "prusa_slicer": shutil.which("prusa-slicer") or shutil.which("PrusaSlicer"),
        "uvtools": shutil.which("UVtoolsCmd"),
        "mslicer_optional": shutil.which("slicer"),
        "print_ready": False,
        "note": "PATH discovery only; versions, Flatpak installs and formats are not qualified.",
    }


def research_plan(model: Path, profile: Path, work_dir: Path) -> list[list[str]]:
    """Produce argv for a future integration test; this function executes nothing.

    The profile must be a complete, flattened, trusted SLA INI. Never feed an arbitrary
    downloaded profile to a backend (profiles may contain executable post-processing).
    """
    for path in (model, profile):
        if not path.is_file():
            raise ValueError(f"Required input does not exist: {path}")
    if model.suffix.lower() != ".stl" or profile.suffix.lower() != ".ini":
        raise ValueError("Research plans require STL geometry and a trusted SLA INI profile.")
    archive = work_dir.resolve() / "layers.sl1"
    native = work_dir.resolve() / "candidate.pm4n"
    return [
        [
            "prusa-slicer",
            "--load",
            str(profile.resolve()),
            "--export-sla",
            "--output",
            str(archive),
            str(model.resolve()),
        ],
        ["UVtoolsCmd", "convert", str(archive), "pm4n", str(native), "--no-overwrite"],
        ["UVtoolsCmd", "print-properties", str(native)],
        ["UVtoolsCmd", "print-issues", str(native)],
    ]
