"""Shared viewport/slicer placement; source meshes remain untouched."""

import numpy as np
import trimesh

from seesaw.geometry import prepare_mesh


def placed_mesh(mesh, transform):
    result = prepare_mesh(mesh, transform)
    # XY controls refer to the center of the rotated object's bounds.
    result.vertices[:, :2] -= result.bounds.mean(axis=0)[:2] - np.array(
        transform.translation_mm[:2]
    )
    return result


def scene_mesh(mesh, project):
    return trimesh.util.concatenate(
        [placed_mesh(mesh, transform) for transform in (project.transform, *project.copies)]
    )


def check_placement(mesh, build_mm):
    low, high = mesh.bounds
    half = np.asarray(build_mm[:2]) / 2
    if np.any(low[:2] < -half - 1e-5) or np.any(high[:2] > half + 1e-5):
        raise ValueError("Model placement extends outside the selected printer's bed.")
    if low[2] < -1e-5 or high[2] > build_mm[2] + 1e-5:
        raise ValueError("Model placement exceeds the selected printer's height range.")
    if abs(low[2]) > 1e-5:
        raise ValueError(
            "Place the model on the bed; use support generation to elevate resin parts."
        )
