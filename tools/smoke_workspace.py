"""Real desktop test: bundled sample, profiles, editable copies and verified export."""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--printer", choices=["mono4", "mk3s"], default="mk3s")
parser.add_argument("--supports", action="store_true")
parser.add_argument("--full-size", action="store_true")
parser.add_argument("--minimized", action="store_true")
parser.add_argument("--layer-mm", type=float)
parser.add_argument("--tilt", type=float, default=0)
args = parser.parse_args()
root = args.output.resolve()
root.mkdir(parents=True, exist_ok=False)
os.environ["SEESAW_JOB_ROOT"] = str(root / "jobs")
os.environ["XDG_CONFIG_HOME"] = str(root / "config")

from seesaw.app import Window  # noqa: E402
from seesaw.project import load_project, save_project  # noqa: E402

app = QApplication([])
window = Window()
window.show()
if args.minimized:
    window.showMinimized()
window.printer_box.setCurrentIndex(window.printer_box.findData(args.printer))
window.load_test_file()
state = {"phase": "import", "passed": False}
started = time.monotonic()
extension = ".pm4n" if args.printer == "mono4" else ".gcode"


def fail(kind, value, traceback):
    state.update(error=str(value), passed=False)
    window.cancel_slice()
    app.quit()


sys.excepthook = fail


def tick():
    (root / "live.json").write_text(
        json.dumps({"phase": state["phase"], "status": window.status.text()})
    )
    if time.monotonic() - started > 900:
        raise AssertionError("Workspace smoke timed out")
    if state["phase"] == "import" and not window.busy() and window.project:
        assert window.project.printer_id == args.printer
        assert all(
            window.material_box.itemData(i).printer_id == args.printer
            for i in range(window.material_box.count())
        )
        if args.printer == "mono4":
            # Synthetic test exposures, not a calibrated resin recommendation.
            window.exposure.setValue(2.5)
            window.bottom_exposure.setValue(25)
        else:
            window.filament_controls["nozzle_c"].setValue(215)
        if args.layer_mm is not None and args.printer == "mono4":
            from dataclasses import replace

            window.project = window.project.edited(
                settings=replace(window.project.settings, layer_mm=args.layer_mm)
            )
            window.sync_controls()
        window.supports.setChecked(args.supports)
        QInputDialog.getText = lambda *a, **k: ("Smoke material profile", True)
        window.save_material_profile()
        assert window.project.material.name == "Smoke material profile"
        if not args.full_size:
            window.scale.setValue(0.25)
            window.rotation[2].setValue(30)
            window.position[0].setValue(-15)
            window.transform_model()
            window.duplicate_model()
            assert len(window.project.copies) == 1
            window.arrange_models()
            window.position[1].setValue(10)
            window.transform_model()
            assert window.project.copies[0].translation_mm[1] == 10
            assert window.project.transform.translation_mm[1] != 10
        if args.tilt:
            window.rotation[0].setValue(args.tilt)
            window.transform_model()
        saved = root / "sample.seesaw"
        save_project(window.project, saved)
        assert load_project(saved).fingerprint() == window.project.fingerprint()
        if not args.minimized:
            window.grab().save(str(root / "prepare.png"))
            window.viewport.screenshot(str(root / "models.png"))
        window.import_model(saved, project_file=True)
        state["phase"] = "reopen"
    elif state["phase"] == "reopen" and not window.busy():
        assert len(window.project.copies) == (0 if args.full_size else 1)
        assert window.project.material.name == "Smoke material profile"
        window.start_slice()
        state["phase"] = "slice"
    elif state["phase"] == "slice" and not window.busy():
        if window.candidate is None:
            if window.status.text().startswith("No export available"):
                raise AssertionError(window.status.text())
            return
        state["phase"] = "preview"
    elif state["phase"] == "preview" and window.export.isEnabled():
        QFileDialog.getSaveFileName = lambda *a, **k: (str(root / ("exported" + extension)), "")
        QMessageBox.warning = lambda *a, **k: QMessageBox.StandardButton.Yes
        window.export_print()
        state["phase"] = "export"
    elif state["phase"] == "export" and not window.busy():
        assert window.status.text().startswith("Calibration candidate exported"), (
            window.status.text()
        )
        target = root / ("exported" + extension)
        directory, manifest = window.candidate
        assert hashlib.sha256(target.read_bytes()).hexdigest() == manifest["output_sha256"]
        assert manifest["material_profile"]["name"] == "Smoke material profile"
        assert len(manifest["project_inputs"]["copies"]) == (0 if args.full_size else 1)
        state.update(manifest=manifest, job=str(directory))
        window.layer_slider.setValue(manifest["layer_count"] - 1)
        state["phase"] = "last"
    elif (
        state["phase"] == "last"
        and f"Layer {state['manifest']['layer_count']}/" in window.layer_info.text()
    ):
        window.layer_image.pixmap().save(str(root / "last-layer.png"))
        if not args.minimized:
            window.grab().save(str(root / "preview.png"))
        other = "mk3s" if args.printer == "mono4" else "mono4"
        window.printer_box.setCurrentIndex(window.printer_box.findData(other))
        assert window.candidate is None and not window.export.isEnabled()
        assert all(
            window.material_box.itemData(i).printer_id == other
            for i in range(window.material_box.count())
        )
        state.update(passed=True, phase="done", elapsed_s=time.monotonic() - started)
        window.close()
        app.quit()


timer = QTimer()
timer.timeout.connect(tick)
timer.start(200)
app.exec()
(root / "result.json").write_text(json.dumps(state, indent=2))
print(json.dumps(state, indent=2))
assert state["passed"]
