"""Opt-in experimental image workspace, isolated from the offline slicer."""

import json
import os
import secrets
import uuid
from dataclasses import asdict
from pathlib import Path
from threading import Event

import pyvista as pv
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from seesaw.generation import ReliefSettings, cancellable_chat, create_relief

SETUP = """Seesaw Experimental — local generation setup

The ordinary slicer requires neither Tailscale, OpenClaw nor CUDA.

Image relief: available now, CPU only; no weights or training. Brightness becomes
height on a solid flat base. This is not full object reconstruction. Start with
60 mm width, 2 mm base and 3 mm relief; inspect scale and details before slicing.

Existing local model: install OpenClaw on the generation computer, configure your
agent and its local vision/model tools, and enable gateway.http.endpoints.
chatCompletions.enabled. Connect here using its loopback address or HTTPS .ts.net
address and gateway token. Tokens grant operator access; use your own trusted
agent. Seesaw sends the selected image and prompt only when you press Send.
The configured agent decides which model/tools execute. A successful chat does
not prove that a 3D model runtime is installed or qualified.

Tailscale: sign in on both computers and use private Tailscale Serve for the
loopback gateway. Preserve existing Serve routes. Do not use public Funnel.
See https://tailscale.com/docs/features/tailscale-serve
OpenClaw endpoint: https://docs.openclaw.ai/gateway/openai-http-api

Install a pretrained 3D model (not training from scratch):
TRELLIS upstream requires Linux, NVIDIA GPU with at least 16 GB VRAM, CUDA toolkit
and an isolated Python environment. RAM/disk requirements depend on weights and
build dependencies and are not measured by Seesaw. Review license and current
instructions before downloading: https://github.com/microsoft/TRELLIS
The local factory currently allows only separately qualified quantized TRELLIS
below 12 GiB total runtime; native TRELLIS is NOT qualified by this setup guide.
No model weights, CUDA dependencies or install scripts run automatically.

A communication model alone cannot replace a diffusion/3D reconstruction model.
If CUDA is unavailable, continue design conversation and use explicit CPU relief.
Import an STL produced by your external model to preview; normal geometry,
build-volume, support, slicing and output validation still apply. Automatic
remote mesh transfer is not implemented yet. The optional download button installs
a pinned trellis.cpp v0.8.1 CUDA runtime and verified Q4 geometry weights. It needs
9 GiB free disk for setup; the downloaded runtime/weights total about 4 GB.
This profile was tested at 512 resolution on RTX 5060 Ti 16 GB. MeshFix repair
can close generated geometry but may alter details; preview it before slicing.
"""


class GenerationWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, operation, parent):
        super().__init__(parent)
        self.operation = operation

    def run(self):
        try:
            self.completed.emit(self.operation())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.operation = None


class GenerationDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.history = []
        self.image = None
        self.model = None
        self.worker = None
        self.session = uuid.uuid4().hex
        self.discard = False
        self.viewport_closed = False
        self.cancel_event = Event()
        self.config_path = Path.home() / ".config/progretech-seesaw/generation.json"
        self.setWindowTitle("Experimental — Image to 3D / OpenClaw + Tailscale")
        self.resize(1050, 800)
        layout = QVBoxLayout(self)
        note = QLabel(
            "Experimental • CPU image relief available • Full AI reconstruction needs "
            "a separately installed model. Generated geometry must still be sliced and checked."
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        self.endpoint = QLineEdit("http://127.0.0.1:18789")
        self.agent = QLineEdit("imagen")
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("OpenClaw / Tailscale address", self.endpoint)
        form.addRow("Agent ID", self.agent)
        form.addRow("Gateway token (not saved)", self.token)
        layout.addLayout(form)
        self.saved_config = {}
        self.binary = QLineEdit()
        self.weights = QLineEdit()
        try:
            config = json.loads(self.config_path.read_text())
            self.saved_config = config
            self.binary.setText(config.get("binary", ""))
            self.weights.setText(config.get("weights", ""))
        except (OSError, ValueError):
            pass
        form.addRow("Local trellis-cli path", self.binary)
        form.addRow("TRELLIS Q4 weights folder", self.weights)
        self.install_button = QPushButton("Download local 3D runtime + Q4 weights (about 4 GB)")
        self.install_button.clicked.connect(self.install_runtime)
        layout.addWidget(self.install_button)
        requirement = QLabel(
            "Experimental CUDA profile: tested on RTX 5060 Ti 16 GB; "
            "9 GiB free disk for setup. 512 resolution, GPU only. "
            "Other hardware is unqualified. No training from scratch."
        )
        requirement.setWordWrap(True)
        layout.addWidget(requirement)
        self.repair = QCheckBox("Repair generated mesh (may change fine details)")
        self.repair.setChecked(True)
        self.repair.toggled.connect(self.invalidate)
        layout.addWidget(self.repair)
        self.full_generate = QPushButton("Generate / recast 3D from image (CUDA)")
        self.full_generate.clicked.connect(self.generate_full)
        layout.addWidget(self.full_generate)
        row = QHBoxLayout()
        self.choose = QPushButton("Choose 2D image")
        self.choose.clicked.connect(self.choose_image)
        row.addWidget(self.choose)
        setup = QPushButton("Requirements / setup")
        setup.clicked.connect(self.show_setup)
        row.addWidget(setup)
        download = QPushButton("Save setup guide")
        download.clicked.connect(self.save_setup)
        row.addWidget(download)
        self.new = QPushButton("New request")
        self.new.clicked.connect(self.new_request)
        row.addWidget(self.new)
        layout.addLayout(row)
        self.image_label = QLabel("No image selected")
        layout.addWidget(self.image_label)
        self.prompt = QTextEdit()
        self.prompt.setPlaceholderText("Describe the object, intended dimensions, or corrections…")
        self.prompt.setMaximumHeight(90)
        layout.addWidget(self.prompt)
        self.send = QPushButton("Send image + prompt / follow-up")
        self.send.clicked.connect(self.send_prompt)
        layout.addWidget(self.send)
        self.reply = QTextEdit()
        self.reply.setReadOnly(True)
        self.reply.setMaximumHeight(120)
        layout.addWidget(self.reply)
        relief = QHBoxLayout()
        self.width = QDoubleSpinBox()
        self.width.setRange(5, 300)
        self.width.setValue(60)
        self.base = QDoubleSpinBox()
        self.base.setRange(0.5, 20)
        self.base.setValue(2)
        self.depth = QDoubleSpinBox()
        self.depth.setRange(0.1, 30)
        self.depth.setValue(3)
        self.invert = QCheckBox("Dark pixels raised")
        for label, control in (
            ("Width mm", self.width),
            ("Base mm", self.base),
            ("Relief mm", self.depth),
        ):
            relief.addWidget(QLabel(label))
            relief.addWidget(control)
            control.valueChanged.connect(self.invalidate)
        relief.addWidget(self.invert)
        self.invert.toggled.connect(self.invalidate)
        layout.addLayout(relief)
        self.viewport = QtInteractor(self)
        self.viewport.set_background("#eff3f4")
        layout.addWidget(self.viewport.interactor, 1)
        buttons = QHBoxLayout()
        self.generate = QPushButton("Create / recast image relief")
        self.generate.clicked.connect(self.generate_relief)
        buttons.addWidget(self.generate)
        self.external = QPushButton("Preview generated STL…")
        self.external.clicked.connect(self.open_stl)
        buttons.addWidget(self.external)
        self.use = QPushButton("Use model in slicer")
        self.use.setEnabled(False)
        self.use.clicked.connect(self.use_model)
        buttons.addWidget(self.use)
        self.cancel = QPushButton("Discard pending result")
        self.cancel.setEnabled(False)
        self.cancel.clicked.connect(self.discard_result)
        buttons.addWidget(self.cancel)
        layout.addLayout(buttons)
        self.status = QLabel(
            "Offline relief works without a connection. Network requests are opt-in."
        )
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        controls = QWidget()
        controls_layout = QVBoxLayout(controls)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not self.viewport.interactor:
                controls_layout.addItem(item)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        columns = QHBoxLayout()
        columns.addWidget(scroll, 2)
        columns.addWidget(self.viewport.interactor, 3)
        layout.addLayout(columns)

    def invalidate(self):
        self.model = None
        self.use.setEnabled(False)
        self.viewport.clear()

    def choose_image(self):
        name, _ = QFileDialog.getOpenFileName(
            self, "Choose image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if name:
            self.image = Path(name)
            self.image_label.setText(self.image.name)
            self.invalidate()

    def new_request(self):
        self.session = uuid.uuid4().hex
        self.reply.clear()
        self.history.clear()
        self.prompt.clear()
        self.invalidate()
        self.status.setText("New conversation started; selected image retained.")

    def show_setup(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Requirements and local model setup")
        dialog.resize(720, 600)
        layout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(SETUP)
        layout.addWidget(text)
        dialog.exec()

    def save_setup(self):
        name, _ = QFileDialog.getSaveFileName(self, "Save setup guide", "seesaw-ai-setup.txt")
        if name:
            Path(name).write_text(SETUP)
            self.status.setText("Setup guide saved. No packages or model weights installed.")

    def start(self, operation, callback):
        if self.worker and self.worker.isRunning():
            return
        self.discard = False
        self.cancel_event.clear()
        for control in self.controls():
            control.setEnabled(False)
        self.use.setEnabled(False)
        self.cancel.setEnabled(True)
        self.worker = GenerationWorker(operation, self)
        self.worker.completed.connect(lambda value: callback(value) if not self.discard else None)
        self.worker.failed.connect(lambda message: self.status.setText(message))
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def controls(self):
        return (
            self.binary,
            self.weights,
            self.install_button,
            self.full_generate,
            self.repair,
            self.choose,
            self.new,
            self.send,
            self.generate,
            self.external,
            self.width,
            self.base,
            self.depth,
            self.invert,
            self.endpoint,
            self.agent,
            self.token,
            self.prompt,
        )

    def worker_finished(self):
        for control in self.controls():
            control.setEnabled(True)
        self.cancel.setEnabled(False)
        self.use.setEnabled(self.model is not None and not self.discard)

    def discard_result(self):
        self.discard = True
        self.cancel_event.set()
        self.status.setText(
            "Result will be discarded. Remote work may continue; "
            "local waiting is cancelled and remote work may continue."
        )

    def send_prompt(self):
        prompt = self.prompt.toPlainText()
        if not prompt.strip():
            self.status.setText("Enter your request or correction first.")
            return
        base, token, agent = self.endpoint.text(), self.token.text(), self.agent.text()
        session, image = self.session, self.image
        self.status.setText("Waiting for your OpenClaw agent…")
        self.history.append("You: " + prompt)
        self.reply.setPlainText("\n\n".join(self.history)[-100000:])
        arguments = {
            "base": base,
            "token": token,
            "agent": agent,
            "session": session,
            "prompt": prompt,
            "image": str(image) if image else None,
        }
        self.start(lambda: cancellable_chat(arguments, self.cancel_event), self.received)

    def received(self, reply):
        self.history.append("Agent: " + reply)
        self.reply.setPlainText("\n\n".join(self.history)[-100000:])
        self.prompt.clear()
        self.status.setText(
            "Agent replied. Review its output; chat success does not validate a mesh."
        )

    def generation_root(self):
        return Path(
            os.environ.get(
                "SEESAW_GENERATION_ROOT",
                self.saved_config.get(
                    "output_root", str(Path.home() / ".local/share/progretech-seesaw/generation")
                ),
            )
        )

    def install_runtime(self):
        from seesaw.generation_install import install

        self.status.setText("Downloading verified optional runtime and weights…")
        self.start(
            lambda: install(self.generation_root() / "runtimes", self.cancel_event),
            self.runtime_installed,
        )

    def runtime_installed(self, paths):
        binary, weights = paths
        self.binary.setText(str(binary))
        self.weights.setText(str(weights))
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps({**self.saved_config, "binary": str(binary), "weights": str(weights)})
        )
        self.status.setText("Pinned runtime installed. Choose an image to generate a 3D model.")

    def generate_full(self):
        from seesaw.trellis import generate

        if self.image is None:
            self.status.setText("Choose a 2D image first.")
            return
        self.invalidate()
        binary, weights = Path(self.binary.text()), Path(self.weights.text())
        source, width, repair = self.image, self.width.value(), self.repair.isChecked()
        seed = secrets.randbelow(2**31)
        job = self.generation_root() / uuid.uuid4().hex
        self.status.setText(
            f"Generating 3D, seed {seed}. Prompt corrections go to OpenClaw; "
            "this model reconstructs the selected image."
        )
        self.start(
            lambda: generate(
                binary,
                weights,
                source,
                job,
                width_mm=width,
                seed=seed,
                cancel=self.cancel_event,
                repair=repair,
            ),
            self.preview,
        )

    def generate_relief(self):
        if self.image is None:
            self.status.setText("Choose a 2D image first.")
            return
        self.invalidate()
        settings = ReliefSettings(
            self.width.value(), self.base.value(), self.depth.value(), self.invert.isChecked()
        )
        root = Path(
            os.environ.get(
                "SEESAW_GENERATION_ROOT",
                self.saved_config.get(
                    "output_root", str(Path.home() / ".local/share/progretech-seesaw/generation")
                ),
            )
        )
        job = root / uuid.uuid4().hex
        job.mkdir(parents=True)
        output, source = job / "relief.stl", self.image

        def operation():
            result = create_relief(source, output, settings)
            (job / "result.json").write_text(json.dumps({**result, "settings": asdict(settings)}))
            return output

        self.status.setText("Creating closed image relief on CPU…")
        self.start(operation, self.preview)

    def open_stl(self):
        name, _ = QFileDialog.getOpenFileName(self, "Preview generated mesh", "", "STL (*.stl)")
        if name:
            self.preview(Path(name))

    def preview(self, path):
        from seesaw.model import load_stl

        try:
            mesh, info = load_stl(path)
            if not info.watertight:
                raise ValueError("Generated model is open; repair it before importing here.")
            self.viewport.clear()
            faces = pv.PolyData(mesh.vertices, faces=pv.CellArray.from_regular_cells(mesh.faces))
            self.viewport.add_mesh(
                faces,
                color="#009aa6",
                smooth_shading=True,
                ambient=0.15,
                diffuse=0.8,
                specular=0.25,
            )
            self.viewport.reset_camera()
            self.model = path
            self.use.setEnabled(True)
            dims = " × ".join(f"{x:.2f}" for x in info.dimensions_mm)
            self.status.setText(
                f"Closed mesh: {dims} mm. Inspect details; print qualification pending."
            )
        except Exception as exc:
            self.invalidate()
            self.status.setText(str(exc))

    def use_model(self):
        if self.owner.busy():
            self.status.setText("Wait for the current slicing/import job first.")
        elif self.model:
            path = self.model
            self.accept()
            self.owner.import_model(path)

    def done(self, result):
        if self.worker and self.worker.isRunning():
            self.discard_result()
            return
        if not self.viewport_closed:
            self.viewport_closed = True
            self.viewport.render_timer.stop()
            self.viewport.close()
        self.token.clear()
        super().done(result)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.discard_result()
            event.ignore()
        else:
            self.token.clear()
            super().closeEvent(event)

    def reject(self):
        if self.worker and self.worker.isRunning():
            self.discard_result()
            return
        self.token.clear()
        super().reject()


def open_generation(owner):
    if owner.busy():
        QMessageBox.information(owner, "Job running", "Finish the current job before generating.")
        return
    dialog = GenerationDialog(owner)
    dialog.exec()
    dialog.token.clear()
    dialog.deleteLater()
