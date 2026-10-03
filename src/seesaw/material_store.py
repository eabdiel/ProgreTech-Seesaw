"""Local versioned material profiles; no downloaded code or implicit network access."""

import json
import os
import tempfile
from pathlib import Path

from seesaw.fdm_settings import FDMSettings
from seesaw.pipeline import PipelineError, Settings
from seesaw.profiles import MaterialProfile


def builtins():
    return [
        MaterialProfile(
            "anycubic-clear-waterwash",
            "Anycubic clear water-washable (uncalibrated)",
            "resin",
            "mono4",
            {},
            provenance="Owner's material; exact SKU/exposures unset",
        ),
        MaterialProfile("custom-resin", "Custom resin (enter settings)", "resin", "mono4", {}),
        MaterialProfile(
            "generic-pla",
            "Generic PLA — Prusa starting profile",
            "fdm",
            "mk3s",
            {"nozzle_c": 210, "bed_c": 60, "layer_mm": 0.2},
            provenance="PrusaSlicer 2.9.4 PrusaResearch.ini Generic PLA; verify your spool",
        ),
    ]


def settings_for(material):
    if material.technology == "resin":
        candidate = Settings(
            **({"exposure_s": 1, "bottom_exposure_s": 1} | dict(material.parameters))
        )
        try:
            candidate.validate()
        except PipelineError as exc:
            raise ValueError(str(exc)) from exc
        if not {"exposure_s", "bottom_exposure_s"} <= material.parameters.keys():
            return None
        settings = candidate
    else:
        settings = FDMSettings(**material.parameters)
    settings.validate()
    return settings


def directory():
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        / "progretech-seesaw/materials"
    )


def read_material(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError("Material profile exceeds 64 KiB.")

    def distinct(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError("Duplicate material profile field.")
            data[key] = value
        return data

    profile = MaterialProfile.from_dict(json.loads(raw, object_pairs_hook=distinct))
    settings_for(profile)
    return profile


def save_material(profile, path=None):
    settings_for(profile)
    destination = Path(path) if path else directory() / (profile.id + ".json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(profile.to_dict(), allow_nan=False, indent=2).encode()
    if len(raw) > 65536:
        raise ValueError("Material profile exceeds 64 KiB.")
    fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".material-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def catalog():
    result, errors = builtins(), []
    for path in sorted(directory().glob("*.json"))[:128]:
        try:
            result.append(read_material(path))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{path.name}: {exc}")
    return result, errors
