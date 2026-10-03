"""Optional real GUI/backend smoke using synthetic exposure values, never a resin preset."""

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

import trimesh
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from seesaw.app import Window
from seesaw.project import save_project

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--supports", action="store_true")
parser.add_argument("--cancel", action="store_true")
args = parser.parse_args()
root = args.output.resolve()
root.mkdir(parents=True, exist_ok=True)
os.environ["SEESAW_JOB_ROOT"] = str(root / "jobs")
source = root / "small.stl"
if args.supports:
    from qualify_pipeline import asymmetric_fixture

    asymmetric_fixture(source)
else:
    trimesh.creation.box(extents=(3, 4, 1)).export(source)
app = QApplication([])
window = Window()
window.show()
state = {"phase": "import", "passed": False, "heartbeat": 0}
started = time.monotonic()
window.import_model(source)


def tick():
    state["heartbeat"] += 1
    (root / "live.json").write_text(
        json.dumps(
            {
                "phase": state["phase"],
                "status": window.status.text(),
                "busy": window.busy(),
                "candidate": bool(window.candidate),
                "export": window.export.isEnabled(),
                "preview": bool(window.layer_preview),
                "heartbeat": state["heartbeat"],
            }
        )
    )
    if time.monotonic() - started > 900:
        state["error"] = "Integration deadline"
        window.cancel_slice()
        app.quit()
        return
    if state["phase"] == "import" and not window.busy() and window.project:
        window.exposure.setValue(2.5)
        window.bottom_exposure.setValue(25)
        window.supports.setChecked(args.supports)
        if args.supports:
            window.project = window.project.edited(
                settings=replace(window.project.settings, layer_mm=0.1)
            )
            window.rotation[0].setValue(35)
        else:
            window.scale.setValue(1.2)
            window.rotation[2].setValue(90)
        window.transform_model()
        state["dimensions"] = window.info.text()
        project_path = root / "roundtrip.seesaw"
        save_project(window.project, project_path)
        window.import_model(project_path, project_file=True)
        state["phase"] = "reopen"
    elif state["phase"] == "reopen" and not window.busy():
        assert window.project.transform.scale == (1 if args.supports else 1.2)
        assert window.project.settings.exposure_s == 2.5
        window.start_slice()
        window.updates.check()
        assert window.updates.worker is None, "Updater must not run during slicing"
        if args.cancel:
            window.slice_worker.progress.connect(
                lambda stage: window.cancel_slice() if stage == "slice" else None
            )
        state["phase"] = "slice"
    elif state["phase"] == "slice" and not window.busy():
        if not window.candidate:
            if args.cancel and "cancelled" in window.status.text().lower():
                assert not window.export.isEnabled()
                assert not list((root / "jobs").rglob("candidate.pm4n"))
                state.update(passed=True, phase="cancelled", elapsed_s=time.monotonic() - started)
                window.close()
                app.quit()
                return
            if window.status.text().startswith("No export available:"):
                state["error"] = window.status.text()
                app.quit()
            return
        state["phase"] = "preview"
    elif state["phase"] == "preview" and window.export.isEnabled():
        target = root / "exported.pm4n"
        QFileDialog.getSaveFileName = lambda *a, **k: (str(target), "")
        QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.Yes
        target.unlink(missing_ok=True)
        window.export_print()
        state["phase"] = "export"
    elif state["phase"] == "export" and not window.busy():
        target = root / "exported.pm4n"
        if not window.status.text().startswith("Calibration candidate exported"):
            return
        assert target.is_file(), window.status.text()
        directory, manifest = window.candidate
        assert hashlib.sha256(target.read_bytes()).hexdigest() == manifest["output_sha256"]
        state["manifest"] = manifest
        state["job"] = str(directory)
        window.layer_slider.setValue(manifest["layer_count"] - 1)
        state["phase"] = "last-layer"
    elif (
        state["phase"] == "last-layer"
        and not window.preview_worker.isRunning()
        and f"Layer {state['manifest']['layer_count']}/" in window.layer_info.text()
    ):
        assert f"Layer {state['manifest']['layer_count']}/" in window.layer_info.text()
        window.layer_image.pixmap().save(str(root / "layer.png"))
        window.grab().save(str(root / "desktop.png"))
        window.viewport.screenshot(str(root / "viewport.png"))
        window.exposure.setValue(3)
        assert not window.export.isEnabled() and window.candidate is None
        state.update(passed=True, phase="done", elapsed_s=time.monotonic() - started)
        window.close()
        app.quit()


timer = QTimer()
timer.timeout.connect(tick)
timer.start(200)


def fail(kind, value, traceback):
    state.update(passed=False, error=str(value))
    app.quit()


sys.excepthook = fail
app.exec()
(root / "result.json").write_text(json.dumps(state, indent=2))
print(json.dumps(state, indent=2))
assert state["passed"]
