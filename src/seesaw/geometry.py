"""Mesh preparation utilities based on Transform."""

import numpy as np
import trimesh

from seesaw.project import Transform


def prepare_mesh(mesh: trimesh.Trimesh, transform: Transform) -> trimesh.Trimesh:
    """Apply transform steps to mesh and return an independent copy.

    Steps:
    1. Center XY and ground Z (lowest vertex at Z=0).
    2. Apply uniform scale.
    3. Apply XYZ Euler rotations in degrees (X then Y then Z about origin).
    4. Ground rotated geometry to Z=0.
    5. Apply translation_mm.

    Source mesh is never modified. Non-finite coordinates after all steps raise ValueError.
    """
    # Work on a copy
    result = mesh.copy()

    # 1. Center XY and ground Z
    bounds = result.bounds
    center_xy = (bounds[0][:2] + bounds[1][:2]) / 2.0
    result.vertices[:, 0] -= center_xy[0]
    result.vertices[:, 1] -= center_xy[1]
    result.vertices[:, 2] -= bounds[0][2]  # ground lowest Z to 0

    # 2. Apply uniform scale
    result.vertices *= transform.scale

    # 3. Apply XYZ Euler rotations in degrees (X then Y then Z about origin)
    # Convert degrees to radians
    rx, ry, rz = np.radians(transform.rotation_deg)

    # Rotation matrices about origin
    # X rotation
    cx, sx = np.cos(rx), np.sin(rx)
    rx_mat = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float64)

    # Y rotation
    cy, sy = np.cos(ry), np.sin(ry)
    ry_mat = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float64)

    # Z rotation
    cz, sz = np.cos(rz), np.sin(rz)
    rz_mat = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float64)

    # Combined rotation: Z * Y * X (applied in X then Y then Z order to vertices)
    rot_mat = rz_mat @ ry_mat @ rx_mat

    result.vertices = result.vertices @ rot_mat.T

    # 4. Ground rotated geometry to Z=0
    min_z = result.vertices[:, 2].min()
    result.vertices[:, 2] -= min_z

    # 5. Apply translation_mm
    result.vertices[:, 0] += transform.translation_mm[0]
    result.vertices[:, 1] += transform.translation_mm[1]
    result.vertices[:, 2] += transform.translation_mm[2]

    # Reject non-finite coordinates
    if not np.isfinite(result.vertices).all():
        raise ValueError("Transform produced non-finite coordinates.")

    return result
