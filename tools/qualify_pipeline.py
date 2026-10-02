"""Actual-binary integration probe with original asymmetric geometry (no third-party models)."""

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh

from seesaw.pipeline import Settings, run_pipeline


def asymmetric_fixture(path):
    polygon = np.array([(0, 0), (12, 0), (12, 2), (2, 2), (2, 8), (0, 8)])
    vertices = np.vstack(
        (np.column_stack((polygon, np.zeros(6))), np.column_stack((polygon, np.full(6, 0.5))))
    )
    top = [(0, 1, 2), (0, 2, 3), (0, 3, 5), (3, 4, 5)]
    faces = [tuple(reversed(face)) for face in top]
    faces += [tuple(i + 6 for i in face) for face in top]
    for i in range(6):
        j = (i + 1) % 6
        faces.extend([(i, j, j + 6), (i, j + 6, i + 6)])
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    assert mesh.is_watertight and mesh.is_volume
    mesh.export(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--supports", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = args.output / "asymmetric-l.stl"
    asymmetric_fixture(fixture)
    if args.supports:
        mesh = trimesh.load_mesh(fixture)
        mesh.apply_transform(trimesh.transformations.rotation_matrix(np.deg2rad(35), (1, 0, 0)))
        mesh.export(fixture)
    result = run_pipeline(
        fixture,
        args.output / "job",
        Settings(2.5, 25, layer_mm=0.1 if args.supports else 0.05, supports=args.supports),
        progress=lambda stage: print(stage, flush=True),
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
