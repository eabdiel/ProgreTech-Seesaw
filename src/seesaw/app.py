"""Read-only desktop foundation. Export is deliberately unavailable until qualification."""

import os
import sys
from pathlib import Path

import numpy as np
import pyvista as pv
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from seesaw import __version__
from seesaw.model import MONO4, load_stl
from seesaw.update_ui import UpdateButton


class ImportWorker(QThread):
    loaded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, path, parent):
        super().__init__(parent)
        self.path = path

    def run(self):
        try:
            mesh, info = load_stl(self.path)
            self.loaded.emit(mesh, info)
        except Exception as exc:
            self.failed.emit(str(exc))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setWindowTitle(f"ProgreTech Seesaw {__version__} — foundation preview")
        self.resize(1280, 800)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel("ProgreTech Seesaw")
        title.setStyleSheet("font-size: 26px; font-weight: bold")
        header = QHBoxLayout()
        header.addWidget(title, 1)
        self.updates = UpdateButton(self)
        header.addWidget(self.updates)
        layout.addLayout(header)
        layout.addWidget(QLabel("Add model   →   Prepare   →   Preview   →   Export"))
        layout.addWidget(
            QLabel("Foundation preview • Import and inspect STL • Slicing coming next")
        )
        row = QHBoxLayout()
        layout.addLayout(row, 1)
        left = QVBoxLayout()
        row.addLayout(left, 1)
        left.addWidget(QLabel("Your model"))
        self.add = QPushButton("＋ Add STL model")
        self.add.clicked.connect(self.open_model)
        left.addWidget(self.add)
        self.info = QLabel("Choose an STL to inspect.\nSTL units are assumed to be millimetres.")
        self.info.setWordWrap(True)
        left.addWidget(self.info)
        left.addStretch()
        frame = QFrame()
        viewport_layout = QVBoxLayout(frame)
        self.viewport = QtInteractor(frame)
        viewport_layout.addWidget(self.viewport.interactor)
        row.addWidget(frame, 3)
        self.viewport.set_background("#eff3f4")
        self.viewport.add_axes()
        right = QVBoxLayout()
        row.addLayout(right, 1)
        for text in (
            "Print setup",
            MONO4.name,
            "Resin / MSLA • 10K",
            "153.408 × 87.040 × 165 mm",
            "9024 × 5120 pixels",
            "Printer profile: awaiting qualification",
            "Material target: Anycubic clear water-washable resin",
            "Exposure calibration: pending",
            "Rotate view: drag\nZoom: scroll",
        ):
            label = QLabel(text)
            label.setWordWrap(True)
            right.addWidget(label)
        reset = QPushButton("Reset view")
        reset.clicked.connect(self.viewport.reset_camera)
        right.addWidget(reset)
        right.addStretch()
        self.status = QLabel("Offline workspace • No account required")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        export = QPushButton("Print export unavailable — backend qualification pending")
        export.setEnabled(False)
        layout.addWidget(export)
        self.setStyleSheet("""
            QWidget { background: #fafaf8; color: #102243; font-size: 15px; }
            QPushButton { background: #008d98; color: white; padding: 12px;
                          border-radius: 7px; }
            QPushButton:disabled { background: #dfe4e5; color: #526373; }
            QLabel { padding: 6px; }
        """)

    def open_model(self):
        name, _ = QFileDialog.getOpenFileName(self, "Add model", "", "STL models (*.stl *.STL)")
        if name:
            self.import_model(Path(name))

    def import_model(self, path):
        self.add.setEnabled(False)
        self.status.setText("Reading model…")
        self.worker = ImportWorker(path, self)
        self.worker.loaded.connect(self.show_model)
        self.worker.failed.connect(self.import_failed)
        self.worker.finished.connect(lambda: self.add.setEnabled(True))
        self.worker.start()

    def import_failed(self, message):
        self.status.setText(f"Could not import model: {message}")

    def show_model(self, mesh, info):
        # Display a copy centered above the bed. No source geometry is modified.
        vertices = mesh.vertices.copy()
        vertices[:, :2] -= mesh.bounds.mean(axis=0)[:2]
        vertices[:, 2] -= mesh.bounds[0, 2]
        faces = np.column_stack((np.full(len(mesh.faces), 3), mesh.faces)).ravel()
        self.viewport.clear()
        self.viewport.add_mesh(pv.PolyData(vertices, faces), color="#00959d")
        self.viewport.add_mesh(
            pv.Plane(center=(0, 0, -0.1), i_size=MONO4.build_mm[0], j_size=MONO4.build_mm[1]),
            color="#99a6ad",
            style="wireframe",
        )
        self.viewport.view_isometric()
        self.viewport.reset_camera()
        dimensions = " × ".join(f"{x:.2f}" for x in info.dimensions_mm)
        self.info.setText(
            f"{info.name}\n\n{dimensions} mm\n{info.triangles:,} triangles\n"
            f"Watertight: {'yes' if info.watertight else 'no'}"
        )
        fit = (
            "Fits unrotated" if info.fits_unrotated else "Exceeds build volume in this orientation"
        )
        self.status.setText(f"{fit} • Supports and raft not included • Printability not verified")

    def closeEvent(self, event):
        if self.updates.busy():
            self.updates.worker.cancel.set()
            self.status.setText("Waiting for the update operation to finish before closing.")
            event.ignore()
            return
        if self.worker is not None and self.worker.isRunning():
            self.status.setText("Wait for model import to finish before closing.")
            event.ignore()
            return
        self.viewport.close()
        event.accept()


def main():
    # The embedded VTK window is qualified here through X11/XWayland only.
    # Respect an explicit platform override for further portability testing.
    if sys.platform == "linux" and os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    app = QApplication(sys.argv)
    app.setApplicationName("progretech-seesaw")
    app.setDesktopFileName("progretech-seesaw")
    window = Window()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
