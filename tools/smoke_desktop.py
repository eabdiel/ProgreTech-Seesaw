"""Optional desktop smoke; requires a working X11/XWayland display.

Usage: QT_QPA_PLATFORM=xcb uv run python tools/smoke_desktop.py --output /path/to/artifacts
"""

import argparse
from pathlib import Path

import numpy as np
import trimesh
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from seesaw.app import Window

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
fixture = args.output / "smoke-box.stl"
trimesh.creation.box(extents=(15, 20, 10)).export(fixture)
app = QApplication([])
window = Window()
window.show()
window.import_model(fixture)
result = {"passed": False}


def finish():
    try:
        assert "15.00 × 20.00 × 10.00" in window.info.text(), window.info.text()
        assert "Fits unrotated" in window.status.text(), window.status.text()
        pixels = window.viewport.screenshot(str(args.output / "viewport.png"))
        # Require visible teal geometry, rather than accepting a blank image.
        teal = (pixels[:, :, 0] < 60) & (pixels[:, :, 1] > 70) & (pixels[:, :, 2] > 70)
        assert np.count_nonzero(teal) > 100, "Model not visible in rendered framebuffer"
        result["passed"] = True
        print("PASS: threaded STL import, dimensions, fit and nonblank VTK framebuffer")
    finally:
        window.close()
        app.quit()


window.worker.finished.connect(lambda: QTimer.singleShot(1500, finish))
QTimer.singleShot(20000, app.quit)
app.exec()
assert result["passed"], "Desktop smoke failed or timed out"
