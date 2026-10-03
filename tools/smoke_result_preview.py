"""Replay a real validated worker result through desktop preview and verified export."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--project", type=Path, required=True)
parser.add_argument("--pipeline", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
a = parser.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
os.environ["XDG_CONFIG_HOME"] = str(a.output / "config")
from seesaw.app import Window  # noqa: E402
from seesaw.project import Project  # noqa: E402

manifest = json.loads((a.pipeline / "manifest.json").read_text())
assert manifest["status"] == "software_validated_not_print_qualified"
app = QApplication([])
w = Window()
w.show()
w.import_model(a.project, project_file=True)
state = {"phase": "import", "passed": False}


def fail(kind, value, tb):
    state["error"] = str(value)
    app.quit()


sys.excepthook = fail


def tick():
    if state.get("in_tick"):
        return
    state["in_tick"] = True
    try:
        if state["phase"] == "import" and not w.busy():
            assert (
                Project.from_dict(manifest["project_inputs"]).fingerprint()
                == w.project.fingerprint()
            )
            snapshot = w.gate.begin(w.project)
            w.slice_complete(snapshot, a.pipeline, manifest)
            state["phase"] = "preview"
        elif state["phase"] == "preview" and w.export.isEnabled():
            w.grab().save(str(a.output / "preview.png"))
            QFileDialog.getSaveFileName = lambda *x, **k: (str(a.output / "exported.pm4n"), "")
            QMessageBox.warning = lambda *x, **k: QMessageBox.StandardButton.Yes
            w.export_print()
            state["phase"] = "export"
        elif state["phase"] == "export" and not w.busy():
            assert (
                hashlib.sha256((a.output / "exported.pm4n").read_bytes()).hexdigest()
                == manifest["output_sha256"]
            )
            w.layer_slider.setValue(manifest["layer_count"] - 1)
            state["phase"] = "last"
        elif (
            state["phase"] == "last" and f"Layer {manifest['layer_count']}/" in w.layer_info.text()
        ):
            assert w.export.isEnabled()
            w.pixel_repair.setChecked(False)
            assert w.candidate is None and not w.export.isEnabled()
            state.update(
                passed=True,
                phase="done",
                layer_count=manifest["layer_count"],
                repair=manifest.get("repair"),
            )
            w.close()
            app.quit()
    finally:
        state["in_tick"] = False


timer = QTimer()
timer.timeout.connect(tick)
timer.start(200)
QTimer.singleShot(60000, app.quit)
app.exec()
(a.output / "result.json").write_text(json.dumps(state, indent=2))
print(json.dumps(state))
assert state["passed"]
