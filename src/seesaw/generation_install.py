"""User-triggered, pinned optional runtime installation. Never runs upstream installers."""

import hashlib
import json
import shutil
import tarfile
import urllib.request
import uuid
from pathlib import Path
from threading import Event


def install(root: Path, cancel: Event | None = None) -> tuple[Path, Path]:
    manifest = json.loads((Path(__file__).parent / "assets/trellis-runtime.json").read_text())
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < 9 * 1024**3:
        raise ValueError("At least 9 GiB free disk space is needed for this optional setup.")
    stage = root / ("trellis-v0.8.1-" + uuid.uuid4().hex)
    stage.mkdir()

    def fetch(entry, target):
        digest = hashlib.sha256()
        total = 0
        with urllib.request.urlopen(entry["url"], timeout=30) as response, target.open("xb") as out:
            while data := response.read(1024 * 1024):
                if cancel and cancel.is_set():
                    raise ValueError("Model download cancelled.")
                total += len(data)
                if total > 2 * 1024**3:
                    raise ValueError("Model download exceeded its size limit.")
                digest.update(data)
                out.write(data)
        if digest.hexdigest() != entry["sha256"]:
            raise ValueError("Downloaded file failed SHA-256 verification.")

    try:
        archive = stage / "runtime.tar.gz"
        fetch(manifest["runtime"], archive)
        runtime = stage / "runtime"
        runtime.mkdir()
        with tarfile.open(archive) as source:
            members = source.getmembers()
            if sum(x.size for x in members) > 4 * 1024**3 or len(members) > 500:
                raise ValueError("Runtime archive exceeds extraction limits.")
            source.extractall(runtime, filter="data")
        weights = stage / "weights"
        weights.mkdir()
        for entry in manifest["weights"]:
            fetch(entry, weights / entry["name"])
        binary = runtime / "trellis-cli"
        if not binary.is_file():
            raise ValueError("Runtime executable missing after extraction.")
        binary.chmod(0o755)
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2))
        archive.unlink()
        return binary, weights
    except Exception:
        shutil.rmtree(stage)
        raise
