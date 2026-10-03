"""Acceptance checks for local-team project persistence."""

from dataclasses import replace

import pytest
import trimesh

from seesaw.pipeline import Settings
from seesaw.project import Project, Transform, load_project, save_project


@pytest.fixture
def project(tmp_path):
    model = tmp_path / "source.stl"
    trimesh.creation.box(extents=(2, 3, 4)).export(model)
    return Project.from_stl_path(model, settings=Settings(2.5, 25))


def test_settings_roundtrip(project, tmp_path):
    target = tmp_path / "project.json"
    save_project(project, target)
    loaded = load_project(target)
    assert loaded == project
    assert loaded.fingerprint() == project.fingerprint()
    assert replace(project, revision=2).fingerprint() == project.fingerprint()
    assert replace(project, settings=Settings(3, 25)).fingerprint() != project.fingerprint()


@pytest.mark.parametrize("changed", [True, False])
def test_source_integrity_on_reopen(project, tmp_path, changed):
    project = replace(project, settings=None)
    target = tmp_path / "project.json"
    save_project(project, target)
    if changed:
        project.model_path.write_bytes(b"changed")
    else:
        project.model_path.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        load_project(target)


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), 0, -1])
def test_invalid_scale(value):
    with pytest.raises(ValueError):
        Transform((0, 0, 0), (0, 0, 0), value)


def test_invalid_revision(project):
    with pytest.raises(ValueError):
        replace(project, revision=True)


def test_invalid_settings(project):
    with pytest.raises(ValueError):
        replace(project, settings=Settings(float("nan"), 25))


def test_atomic_failed_replace_preserves_file(project, tmp_path, monkeypatch):
    project = replace(project, settings=None)
    target = tmp_path / "project.json"
    save_project(project, target)
    before = target.read_bytes()

    def fail(*args):
        raise OSError("simulated destination failure")

    monkeypatch.setattr("seesaw.project.os.replace", fail)
    with pytest.raises(OSError):
        save_project(replace(project, revision=2), target)
    assert target.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ["project.json", "source.stl"]


def test_unknown_keys_and_schema(project):
    data = replace(project, settings=None).to_dict()
    with pytest.raises(ValueError):
        Project.from_dict({**data, "ready": True})
    with pytest.raises(ValueError):
        Project.from_dict({**data, "schema": "future"})


def test_integer_transform_values_are_valid():
    transform = Transform((0, 1, 2), (0, 90, 0), 1)
    assert transform.translation_mm == (0.0, 1.0, 2.0)


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), 0.0, -1.0])
def test_scale_validation_independent_of_vectors(value):
    with pytest.raises(ValueError):
        Transform((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), value)


@pytest.mark.parametrize("settings", [Settings(True, 25), Settings(2.5, 25, supports=1)])
def test_settings_types_at_construction(project, settings):
    with pytest.raises(ValueError):
        replace(project, settings=settings)


def test_source_overwrite_rejected(project):
    before = project.model_path.read_bytes()
    with pytest.raises(ValueError):
        save_project(project, project.model_path)
    assert project.model_path.read_bytes() == before


@pytest.mark.parametrize("sha", ["+" + "a" * 63, " " + "a" * 63, "A" * 64])
def test_sha256_strict_format(project, sha):
    with pytest.raises(ValueError):
        replace(project, model_sha256=sha)


def test_duplicate_saved_fields_rejected(project, tmp_path):
    import json

    target = tmp_path / "duplicate.json"
    data = json.dumps(project.to_dict())
    target.write_text('{"revision": 9, ' + data[1:])
    with pytest.raises(ValueError):
        load_project(target)


def test_empty_settings_rejected(project):
    with pytest.raises(ValueError):
        Project.from_dict({**project.to_dict(), "settings": {}})


def test_saved_readiness_rejected(project):
    with pytest.raises(ValueError):
        Project.from_dict({**project.to_dict(), "export_ready": True})


def test_stale_and_superseded_job_results(project):
    from seesaw.project import JobGate

    gate = JobGate()
    first = gate.begin(project)
    edited = project.edited(settings=Settings(3.0, 25.0))
    second = gate.begin(edited)
    assert not gate.finish(edited, first)
    assert gate.active == second
    assert gate.finish(edited, second)
    assert gate.is_current(edited)
    assert not gate.is_current(project)
    gate.invalidate()
    assert not gate.is_current(edited)


def test_source_changes_invalidate_completed_result(project):
    from seesaw.project import JobGate

    gate = JobGate()
    token = gate.begin(project)
    assert gate.finish(project, token)
    project.model_path.write_bytes(b"changed")
    assert not gate.is_current(project)


def test_save_reopen_does_not_restore_job_state(project, tmp_path):
    from seesaw.project import JobGate

    gate = JobGate()
    assert gate.finish(project, gate.begin(project))
    target = tmp_path / "project.json"
    save_project(project, target)
    assert not JobGate().is_current(load_project(target))


def test_large_project_json_rejected(tmp_path):
    target = tmp_path / "large.json"
    target.write_bytes(b" " * (65536 + 1))
    with pytest.raises(ValueError, match="64 KiB"):
        load_project(target)


def test_integer_and_float_settings_fingerprints_match(project):
    assert project.fingerprint() == replace(project, settings=Settings(2.5, 25.0)).fingerprint()
