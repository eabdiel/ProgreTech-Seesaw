"""Display retained failed-job layers without granting export readiness."""

import argparse
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project", required=True, type=Path)
parser.add_argument("--job", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
os.environ["XDG_CONFIG_HOME"] = str(args.output / "config")
from seesaw.app import Window  # noqa: E402
from seesaw.project import load_project, save_project  # noqa: E402

app = QApplication([])
window = Window()
window.show()
window.import_model(args.project, project_file=True)
state = {"phase": "import", "passed": False}


def fail(kind, value, trace):
    state.update(error=str(value))
    app.quit()


sys.excepthook = fail


def tick():
    if state["phase"] == "import" and not window.busy():
        window.job_directory = args.job
        window.slice_failed("UVTools reported issues; inspect issues.log before proceeding.")
        assert window.candidate is None and not window.export.isEnabled()
        assert window.finding_box.count() > 1
        window.finding_box.setCurrentIndex(1)
        state["phase"] = "preview"
    elif state["phase"] == "preview" and "Inspection only" in window.layer_info.text():
        assert not window.export.isEnabled()
        window.grab().save(str(args.output / "findings.png"))
        window.layer_image.pixmap().save(str(args.output / "finding-crop.png"))
        window.pixel_repair.setChecked(True)
        assert window.project.repair_single_pixels
        assert window.layer_preview is None and not window.export.isEnabled()
        saved = args.output / "repair-choice.seesaw"
        save_project(window.project, saved)
        assert load_project(saved).repair_single_pixels
        state.update(passed=True, phase="done")
        window.close()
        app.quit()


timer = QTimer()


def guarded_tick():
    if state.get("in_tick"):
        return
    state["in_tick"] = True
    try:
        tick()
    finally:
        state["in_tick"] = False


timer.timeout.connect(guarded_tick)
timer.start(200)
QTimer.singleShot(30000, app.quit)
app.exec()
(args.output / "result.json").write_text(json.dumps(state, indent=2))
print(json.dumps(state))
assert state["passed"]
