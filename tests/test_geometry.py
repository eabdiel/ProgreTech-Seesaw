"""Tests for geometry module."""

import warnings

import numpy as np
import pytest
import trimesh

from seesaw.geometry import prepare_mesh
from seesaw.project import Transform


@pytest.fixture
def simple_box():
    """Create a simple box mesh at [10, 20, 30] to [20, 30, 40]."""
    vertices = [
        [10.0, 20.0, 30.0],
        [20.0, 20.0, 30.0],
        [20.0, 30.0, 30.0],
        [10.0, 30.0, 30.0],
        [10.0, 20.0, 40.0],
        [20.0, 20.0, 40.0],
        [20.0, 30.0, 40.0],
        [10.0, 30.0, 40.0],
    ]
    faces = [
        [0, 1, 2],
        [0, 2, 3],
        [1, 5, 6],
        [1, 6, 2],
        [5, 4, 7],
        [5, 7, 6],
        [4, 0, 3],
        [4, 3, 7],
        [3, 2, 6],
        [3, 6, 7],
        [4, 5, 1],
        [4, 1, 0],
    ]
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    return mesh


def test_source_unchanged(simple_box):
    """Source mesh should remain unchanged after prepare_mesh."""
    original_vertices = simple_box.vertices.copy()
    transform = Transform()
    result = prepare_mesh(simple_box, transform)
    assert np.allclose(simple_box.vertices, original_vertices)
    assert not np.allclose(simple_box.vertices, result.vertices)


def test_centering_and_grounding(simple_box):
    """Test XY centering and Z grounding."""
    transform = Transform()
    result = prepare_mesh(simple_box, transform)

    # After centering XY, centroid should be at origin in XY
    center_xy = result.vertices[:, :2].mean(axis=0)
    assert np.allclose(center_xy, [0.0, 0.0], atol=1e-6)

    # After grounding, min Z should be 0
    assert np.isclose(result.vertices[:, 2].min(), 0.0, atol=1e-6)


def test_scale_applied(simple_box):
    """Test uniform scale is applied correctly."""
    scale = 2.5
    transform = Transform(scale=scale)
    result = prepare_mesh(simple_box, transform)

    # After centering/grounding, original vertices became relative to [15, 25, 30] ground 0
    # Original dimensions: 10x10x10, after scale should be 25x25x25
    extents = result.vertices.max(axis=0) - result.vertices.min(axis=0)
    assert np.allclose(extents, [25.0, 25.0, 25.0], atol=1e-6)


def test_rotation_order_X_then_Y_then_Z(simple_box):
    """Test rotation order is X then Y then Z about origin with non-cubic box."""
    # Use a non-cubic box (2,4,6) with process=False for stable vertices
    mesh = trimesh.creation.box(extents=(2, 4, 6))

    transform = Transform(rotation_deg=(90.0, 90.0, 90.0))
    result = prepare_mesh(mesh, transform)

    # trimesh.creation.box(extents=(2,4,6)) creates vertices in bounds [-1,1]x[-2,2]x[-3,3]
    # After center/ground: Z goes from 0 to 6, vertices at (±1, ±2, 0) and (±1, ±2, 6)
    # After X90 Y90 Z90 rotation (z, y, -x): then ground to Z=0 (add 1 to Z):
    # (1, 2, 0) -> (0, 2, -1) -> (0, 2, 0)
    # (1, 2, 6) -> (6, 2, -1) -> (6, 2, 0)
    # (-1, 2, 0) -> (0, 2, 1) -> (0, 2, 2)
    # (-1, 2, 6) -> (6, 2, 1) -> (6, 2, 2)
    # (1, -2, 0) -> (0, -2, -1) -> (0, -2, 0)
    # (1, -2, 6) -> (6, -2, -1) -> (6, -2, 0)
    # (-1, -2, 0) -> (0, -2, 1) -> (0, -2, 2)
    # (-1, -2, 6) -> (6, -2, 1) -> (6, -2, 2)
    expected_vertices = np.array([
        [ 0.0, -2.0,  2.0],  # (-1,-2,0) -> (0,-2,1) -> (0,-2,2)
        [ 6.0, -2.0,  2.0],  # (-1,-2,6) -> (6,-2,1) -> (6,-2,2)
        [ 0.0,  2.0,  2.0],  # (-1,2,0) -> (0,2,1) -> (0,2,2)
        [ 6.0,  2.0,  2.0],  # (-1,2,6) -> (6,2,1) -> (6,2,2)
        [ 0.0, -2.0,  0.0],  # (1,-2,0) -> (0,-2,-1) -> (0,-2,0)
        [ 6.0, -2.0,  0.0],  # (1,-2,6) -> (6,-2,-1) -> (6,-2,0)
        [ 0.0,  2.0,  0.0],  # (1,2,0) -> (0,2,-1) -> (0,2,0)
        [ 6.0,  2.0,  0.0],  # (1,2,6) -> (6,2,-1) -> (6,2,0)
    ])
    for i, expected in enumerate(expected_vertices):
        assert np.allclose(result.vertices[i], expected, atol=1e-6), f"Vertex {i} mismatch"


def test_translation_applied(simple_box):
    """Test translation_mm is applied correctly."""
    transform = Transform(translation_mm=(10.0, 20.0, 30.0))
    result = prepare_mesh(simple_box, transform)

    # After centering/grounding, mesh is centered at origin with min Z = 0
    # Then translation moves it
    center_xy = result.vertices[:, :2].mean(axis=0)
    assert np.allclose(center_xy, [10.0, 20.0], atol=1e-6)
    assert np.isclose(result.vertices[:, 2].min(), 30.0, atol=1e-6)


def test_negative_translation_retained(simple_box):
    """Test negative translation values are applied correctly."""
    transform = Transform(translation_mm=(-15.0, -25.0, -10.0))
    result = prepare_mesh(simple_box, transform)

    # After centering/grounding, translate to negative coordinates
    center_xy = result.vertices[:, :2].mean(axis=0)
    assert np.allclose(center_xy, [-15.0, -25.0], atol=1e-6)
    # Min Z after grounding + translation
    assert np.isclose(result.vertices[:, 2].min(), -10.0, atol=1e-6)


def test_asymmetric_fixture_orientation():
    """Test orientation with asymmetric dimensions."""
    # Create an asymmetric box: 20x10x5
    vertices = [
        [0.0, 0.0, 0.0],
        [20.0, 0.0, 0.0],
        [20.0, 10.0, 0.0],
        [0.0, 10.0, 0.0],
        [0.0, 0.0, 5.0],
        [20.0, 0.0, 5.0],
        [20.0, 10.0, 5.0],
        [0.0, 10.0, 5.0],
    ]
    faces = [
        [0, 1, 2],
        [0, 2, 3],
        [1, 5, 6],
        [1, 6, 2],
        [5, 4, 7],
        [5, 7, 6],
        [4, 0, 3],
        [4, 3, 7],
        [3, 2, 6],
        [3, 6, 7],
        [4, 5, 1],
        [4, 1, 0],
    ]
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    original_extents = mesh.vertices.max(axis=0) - mesh.vertices.min(axis=0)

    # Center and ground (already grounded at Z=0)
    transform = Transform(translation_mm=(5.0, 5.0, 0.0))
    result = prepare_mesh(mesh, transform)

    # After centering: center at origin, so vertices span [-10, 10] in X, [-5, 5] in Y, [0, 5] in Z
    # Then translation adds (5, 5, 0)

    # Check dimensions are preserved
    result_extents = result.vertices.max(axis=0) - result.vertices.min(axis=0)
    assert np.allclose(result_extents, original_extents, atol=1e-6)

    # Check center after centering is at origin
    center_xy = result.vertices[:, :2].mean(axis=0)
    assert np.allclose(center_xy, [5.0, 5.0], atol=1e-6)


def test_nonfinite_rejected():
    """Test that non-finite coordinates after transform raise ValueError."""
    # Use trimesh.creation.box(extents=(10,10,10)) and Transform(scale=1e308)
    # The resulting coordinates will be nonfinite (inf), triggering ValueError
    mesh = trimesh.creation.box(extents=(10, 10, 10))
    transform = Transform(scale=1e308)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(ValueError, match="non-finite"):
            prepare_mesh(mesh, transform)
