"""Read-only STL inspection. Printer dimensions are provisional until hardware qualification."""

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import trimesh


@dataclass(frozen=True)
class Printer:
    name: str = "Anycubic Photon Mono 4"
    build_mm: tuple[float, float, float] = (153.408, 87.040, 165.0)
    resolution_px: tuple[int, int] = (9024, 5120)
    extension: str = ".pm4n"
    qualified: bool = False


MONO4 = Printer()


@dataclass(frozen=True)
class Inspection:
    name: str
    dimensions_mm: tuple[float, float, float]
    triangles: int
    watertight: bool
    fits_unrotated: bool

    def to_dict(self):
        return asdict(self)


def load_stl(path: Path) -> tuple[trimesh.Trimesh, Inspection]:
    path = path.expanduser().resolve(strict=True)
    if path.suffix.lower() != ".stl":
        raise ValueError(
            "This foundation supports STL only; dimensions are interpreted as millimetres."
        )
    if path.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("STL exceeds the foundation's 256 MiB import limit.")
    mesh = trimesh.load_mesh(path, file_type="stl", process=True)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ValueError("The file does not contain a triangle mesh.")
    if not np.isfinite(mesh.vertices).all():
        raise ValueError("Mesh contains non-finite coordinates.")
    if np.any(mesh.extents <= 0):
        raise ValueError("Mesh must have positive dimensions on all three axes.")
    dimensions = tuple(float(x) for x in mesh.extents)
    return mesh, Inspection(
        name=path.name,
        dimensions_mm=dimensions,
        triangles=len(mesh.faces),
        watertight=bool(mesh.is_watertight),
        fits_unrotated=all(a <= b for a, b in zip(dimensions, MONO4.build_mm, strict=True)),
    )
