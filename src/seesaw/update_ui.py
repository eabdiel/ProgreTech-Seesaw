"""Qt update workflow; admin authentication is delegated to Ubuntu PolicyKit."""

import os
import shutil
import subprocess
from pathlib import Path
from threading import Event

from PySide6.QtCore import QProcess, QThread, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from seesaw import __version__
from seesaw.updates import check_latest, download_release

INSTALLER = Path("/usr/lib/progretech-seesaw/install-update")


class UpdateWorker(QThread):
    checked = Signal(object)
    status = Signal(str)
    installed = Signal()
    failed = Signal(str)

    def __init__(self, parent, release=None):
        super().__init__(parent)
        self.release = release
        self.cancel = Event()

    def run(self):
        downloaded = None
        try:
            if self.release is None:
                self.checked.emit(check_latest(__version__))
                return
            cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "seesaw"
            downloaded = download_release(
                self.release,
                cache,
                self.cancel,
                lambda pct: self.status.emit(f"Downloading update… {pct}%"),
            )
            if self.cancel.is_set():
                return
            self.status.emit("Installing update — authenticate in the Ubuntu dialog…")
            result = subprocess.run(
                [
                    "/usr/bin/pkexec",
                    str(INSTALLER),
                    str(downloaded),
                    self.release.version,
                    self.release.sha256,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                raise RuntimeError(
                    "Update was not installed. Authentication may have been cancelled, "
                    "or another package operation is running.\n" + result.stderr[-1200:]
                )
            self.installed.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            if downloaded:
                shutil.rmtree(downloaded.parent, ignore_errors=True)


class UpdateButton(QPushButton):
    def __init__(self, window):
        super().__init__("Check for updates", window)
        self.window = window
        self.worker = None
        self.clicked.connect(self.check)

    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def check(self):
        if self.busy():
            return
        if self.window.busy() or (
            self.window.preview_worker is not None and self.window.preview_worker.isRunning()
        ):
            self.window.status.setText("Finish the current job before checking for updates.")
            return
        self.setEnabled(False)
        self.window.job_controls(False)
        self.window.cancel.setEnabled(False)
        self.window.status.setText("Checking published GitHub releases…")
        self.worker = UpdateWorker(self)
        self.worker.checked.connect(self.on_checked)
        self.worker.failed.connect(self.on_failed)
        worker = self.worker
        worker.finished.connect(lambda: self.enable_after(worker))
        self.worker.start()

    def on_checked(self, release):
        if release is None:
            self.window.status.setText(f"Seesaw {__version__} is up to date.")
            return
        self.window.status.setText(f"Seesaw {release.version} is available.")
        if not INSTALLER.is_file():
            QMessageBox.information(
                self.window,
                "Update available",
                f"Version {release.version} is available. Install the Ubuntu .deb release "
                "to enable self-updates. Development checkouts are never modified.",
            )
            return
        answer = QMessageBox.question(
            self.window,
            "Install Seesaw update?",
            f"Update {__version__} → {release.version}?\n"
            f"Download: {release.size / 1024**2:.0f} MiB. Ubuntu will ask for administrator "
            "authentication. Restart Seesaw after installation.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        # The check worker can still be completing its signal delivery. Keep it owned,
        # and finish it before replacing the reference with the install worker.
        self.worker.wait()
        self.setEnabled(False)
        self.window.job_controls(False)
        self.window.cancel.setEnabled(False)
        self.worker = UpdateWorker(self, release)
        self.worker.status.connect(self.window.status.setText)
        self.worker.failed.connect(self.on_failed)
        self.worker.installed.connect(self.on_installed)
        worker = self.worker
        worker.finished.connect(lambda: self.enable_after(worker))
        self.worker.start()

    def enable_after(self, worker):
        if self.worker is worker:
            self.setEnabled(True)
            self.window.job_controls(True)

    def on_failed(self, message):
        self.window.status.setText(message)
        QMessageBox.warning(self.window, "Update unavailable", message)

    def on_installed(self):
        self.window.status.setText("Update installed. Restart Seesaw to use the new version.")
        answer = QMessageBox.question(
            self.window,
            "Update installed",
            "Restart Seesaw now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.worker.wait()
            started = QProcess.startDetached("/usr/bin/progretech-seesaw", [])[0]
            if started:
                QApplication.instance().quit()
            else:
                self.window.status.setText("Restart failed. Open Seesaw from the launcher.")
