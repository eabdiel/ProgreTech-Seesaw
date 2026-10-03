"""Actual Qt/VTK relief generation, preview, import and stale-result smoke."""

import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
os.environ['SEESAW_GENERATION_ROOT'] = str(args.output / 'jobs')
from seesaw.app import Window  # noqa: E402
from seesaw.generation_ui import GenerationDialog  # noqa: E402

app = QApplication([])
window = Window()
window.show()
dialog = GenerationDialog(window)
dialog.show()
source = args.output / 'fixture.png'
Image.linear_gradient('L').resize((80, 60)).save(source)
dialog.image = source
dialog.generate_relief()
state = {'phase': 'generate', 'passed': False}


def fail(kind, error, trace):
    state['error'] = str(error)
    app.quit()


sys.excepthook = fail


def tick():
    if state.get('inside'):
        return
    state['inside'] = True
    try:
        if state['phase'] == 'generate' and dialog.model and not dialog.worker.isRunning():
            dialog.viewport.screenshot(str(args.output / 'relief-preview.png'))
            model = dialog.model
            dialog.width.setValue(65)
            assert dialog.model is None and not dialog.use.isEnabled()
            dialog.preview(model)
            dialog.use_model()
            state['phase'] = 'import'
        elif state['phase'] == 'import' and window.project and not window.busy():
            assert window.inspection.watertight
            assert not window.export.isEnabled()
            state.update(passed=True, phase='done')
            window.close()
            app.quit()
    finally:
        state['inside'] = False


timer = QTimer()
timer.timeout.connect(tick)
timer.start(200)
QTimer.singleShot(30000, app.quit)
app.exec()
(args.output / 'result.json').write_text(json.dumps(state, indent=2))
print(json.dumps(state))
assert state['passed']
