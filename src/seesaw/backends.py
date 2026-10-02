"""Backend discovery and research command plans, never an implicit print/export API."""

import os
import shutil
from pathlib import Path


def find_uvtools() -> str | None:
    direct = shutil.which("UVtoolsCmd")
    packaged = Path("/usr/lib/uvtools/UVtoolsCmd")
    return direct or (
        str(packaged) if packaged.is_file() and os.access(packaged, os.X_OK) else None
    )


def discover() -> dict:
    return {
        "prusa_slicer": shutil.which("prusa-slicer") or shutil.which("PrusaSlicer"),
        "uvtools": find_uvtools(),
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
    uvtools = find_uvtools() or "UVtoolsCmd"
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
        [uvtools, "convert", str(archive), "pm4n", str(native), "--no-overwrite"],
        [uvtools, "print-properties", str(native)],
        [uvtools, "print-issues", str(native)],
    ]
