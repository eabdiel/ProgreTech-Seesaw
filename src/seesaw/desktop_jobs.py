"""Desktop job orchestration; published files remain unqualified hardware candidates."""

from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread, Signal

from seesaw.geometry import prepare_mesh
from seesaw.model import load_stl
from seesaw.pipeline import PipelineError, run_pipeline


class SliceWorker(QThread):
    progress = Signal(str)
    succeeded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, project, root, parent=None):
        super().__init__(parent)
        self.project = project
        self.root = Path(root)
        self.cancel = Event()

    def run(self):
        try:
            project = self.project
            if project.settings is None:
                raise ValueError("Enter explicit resin exposure settings first.")
            if any(project.transform.translation_mm):
                raise ValueError("Translated projects are not yet qualified for slicing.")
            project.verify_source()
            mesh, _ = load_stl(project.model_path)
            project.verify_source()
            prepared = prepare_mesh(mesh, project.transform)
            self.root.mkdir(parents=True, exist_ok=False)
            source = self.root / "prepared.stl"
            prepared.export(source)
            if self.cancel.is_set():
                raise PipelineError("Job cancelled.")
            directory = self.root / "pipeline"
            manifest = run_pipeline(
                source, directory, project.settings, self.cancel, self.progress.emit
            )
            if self.cancel.is_set():
                raise PipelineError("Job cancelled.")
            project.verify_source()
            self.succeeded.emit(directory, manifest)
        except Exception as exc:
            self.failed.emit(str(exc))


class PreviewWorker(QThread):
    loaded = Signal(int, bytes)
    failed = Signal(str)

    def __init__(self, preview, index, parent=None):
        super().__init__(parent)
        self.preview, self.index = preview, index

    def run(self):
        try:
            self.loaded.emit(self.index, self.preview.thumbnail(self.index))
        except Exception as exc:
            self.failed.emit(str(exc))


class ExportWorker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, project, source, destination, expected_hash, parent=None):
        super().__init__(parent)
        self.project = project
        self.source, self.destination, self.expected_hash = source, destination, expected_hash
        self.cancel = Event()

    def run(self):
        from seesaw.export import export_candidate

        try:
            self.project.verify_source()
            export_candidate(
                self.source,
                self.destination,
                self.expected_hash,
                self.cancel,
                self.project.verify_source,
            )
            self.succeeded.emit(str(self.destination))
        except Exception as exc:
            self.failed.emit(str(exc))
