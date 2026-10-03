"""Versioned, technology-bound profiles; numerical ranges belong to adapters."""

import math
import re
from dataclasses import dataclass
from types import MappingProxyType


def text(value, label, limit=300):
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise ValueError(f"{label} must be bounded nonempty text.")


def identity(value):
    text(value, "Profile ID", 64)
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Profile ID must be a lowercase ASCII slug.")


def finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def revision(value):
    if type(value) is not int or value < 1:
        raise ValueError("Revision must be a positive integer.")


@dataclass(frozen=True)
class PrinterProfile:
    id: str
    name: str
    technology: str
    build_mm: tuple[float, float, float]
    extension: str
    provenance: str
    revision: int = 1

    def __post_init__(self):
        identity(self.id)
        text(self.name, "Printer name")
        text(self.provenance, "Provenance")
        revision(self.revision)
        if self.technology not in ("resin", "fdm"):
            raise ValueError("Unknown printer technology.")
        if (
            type(self.build_mm) is not tuple
            or len(self.build_mm) != 3
            or not all(finite(v) and v > 0 for v in self.build_mm)
        ):
            raise ValueError("Build dimensions must be three positive finite numbers.")
        if self.extension != {"resin": ".pm4n", "fdm": ".gcode"}[self.technology]:
            raise ValueError("Output format does not match the printer technology.")


PRINTERS = (
    PrinterProfile(
        "mono4",
        "Anycubic Photon Mono 4",
        "resin",
        (153.408, 87.04, 165.0),
        ".pm4n",
        "UVTools core 7.0.1 machine table; physical qualification pending",
    ),
    PrinterProfile(
        "mk3s",
        "Original Prusa i3 MK3S / MK3S+ (0.4 mm)",
        "fdm",
        (250.0, 210.0, 210.0),
        ".gcode",
        "PrusaSlicer 2.9.4 PrusaResearch.ini; physical qualification pending",
    ),
)


def printer_by_id(identifier):
    for printer in PRINTERS:
        if type(identifier) is str and identifier == printer.id:
            return printer
    raise ValueError("Unknown printer profile.")


@dataclass(frozen=True)
class MaterialProfile:
    id: str
    name: str
    technology: str
    printer_id: str
    parameters: dict
    revision: int = 1
    provenance: str = "User supplied; calibration not verified"

    def __post_init__(self):
        identity(self.id)
        text(self.name, "Material name")
        text(self.provenance, "Provenance")
        revision(self.revision)
        if printer_by_id(self.printer_id).technology != self.technology:
            raise ValueError("Material technology does not match its printer.")
        if not isinstance(self.parameters, (dict, MappingProxyType)):
            raise ValueError("Material parameters must be an object.")
        allowed = (
            {
                "exposure_s",
                "bottom_exposure_s",
                "layer_mm",
                "bottom_layers",
                "lift_mm",
                "lift_mm_min",
                "retract_mm_min",
                "rest_s",
                "supports",
                "antialias",
            }
            if self.technology == "resin"
            else {"layer_mm", "nozzle_c", "bed_c", "infill_percent", "speed_mm_s", "supports"}
        )
        for key, value in self.parameters.items():
            if key not in allowed:
                raise ValueError(f"Unknown material parameter: {key}")
            if key in ("supports", "antialias"):
                valid = type(value) is bool
            elif key == "bottom_layers":
                valid = type(value) is int
            else:
                valid = finite(value)
            if not valid:
                raise ValueError(f"Invalid material parameter type/value: {key}")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))

    def to_dict(self):
        return {
            "schema": "seesaw-material-v1",
            "id": self.id,
            "name": self.name,
            "technology": self.technology,
            "printer_id": self.printer_id,
            "parameters": dict(self.parameters),
            "revision": self.revision,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data):
        keys = {
            "schema",
            "id",
            "name",
            "technology",
            "printer_id",
            "parameters",
            "revision",
            "provenance",
        }
        if type(data) is not dict or set(data) != keys or data["schema"] != "seesaw-material-v1":
            raise ValueError("Unsupported material schema or missing/extra fields.")
        return cls(**{key: value for key, value in data.items() if key != "schema"})


def materials_for_printer(profiles, printer_id):
    technology = printer_by_id(printer_id).technology
    return [p for p in profiles if p.printer_id == printer_id and p.technology == technology]
