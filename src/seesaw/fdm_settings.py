"""Explicit filament settings, separate from resin exposure and motion."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FDMSettings:
    layer_mm: float = 0.2
    nozzle_c: float = 210.0
    bed_c: float = 60.0
    infill_percent: float = 15.0
    speed_mm_s: float = 40.0
    supports: bool = False

    def validate(self):
        for field, low, high in (
            ("layer_mm", 0.05, 0.3),
            ("nozzle_c", 170, 280),
            ("bed_c", 0, 110),
            ("infill_percent", 0, 100),
            ("speed_mm_s", 5, 100),
        ):
            value = getattr(self, field)
            if (
                type(value) not in (int, float)
                or not low <= value <= high
                or not math.isfinite(value)
            ):
                raise ValueError(f"{field} must be a finite number between {low} and {high}.")
        if type(self.supports) is not bool:
            raise ValueError("supports must be boolean.")
