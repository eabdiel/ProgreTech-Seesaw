import hashlib

import pytest

from seesaw.export import export_candidate


def test_verified_export_and_tamper_preserves_destination(tmp_path):
    source = tmp_path / "candidate.pm4n"
    source.write_bytes(b"validated fixture")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    target = tmp_path / "usb.pm4n"
    export_candidate(source, target, digest)
    assert target.read_bytes() == source.read_bytes()
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        export_candidate(source, target, digest)
    assert target.read_bytes() == b"validated fixture"
    assert not list(tmp_path.glob(".seesaw-export-*"))


def test_wrong_extension_and_source_destination_rejected(tmp_path):
    source = tmp_path / "candidate.pm4n"
    source.write_bytes(b"data")
    digest = hashlib.sha256(b"data").hexdigest()
    for target in (source, tmp_path / "model.stl"):
        with pytest.raises(ValueError):
            export_candidate(source, target, digest)
    assert source.read_bytes() == b"data"


def test_failed_publication_preserves_previous_file(tmp_path, monkeypatch):
    import seesaw.export as module

    source, target = tmp_path / "candidate.pm4n", tmp_path / "saved.pm4n"
    source.write_bytes(b"new")
    target.write_bytes(b"old")

    def fail(*args):
        raise OSError("USB removed")

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError, match="USB removed"):
        export_candidate(source, target, hashlib.sha256(b"new").hexdigest())
    assert target.read_bytes() == b"old"
    assert not list(tmp_path.glob(".seesaw-export-*"))


def test_cancel_or_changed_inputs_never_publish(tmp_path):
    from threading import Event

    source, target = tmp_path / "candidate.pm4n", tmp_path / "saved.pm4n"
    source.write_bytes(b"new")
    target.write_bytes(b"old")
    cancelled = Event()
    cancelled.set()
    with pytest.raises(ValueError, match="cancelled"):
        export_candidate(source, target, hashlib.sha256(b"new").hexdigest(), cancelled)

    def changed():
        raise ValueError("Source changed")

    with pytest.raises(ValueError, match="Source changed"):
        export_candidate(source, target, hashlib.sha256(b"new").hexdigest(), verify_inputs=changed)
    assert target.read_bytes() == b"old"
    assert not list(tmp_path.glob(".seesaw-export-*"))
