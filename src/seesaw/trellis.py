"""Optional, explicit local TRELLIS.cpp geometry adapter; weights are user managed."""

import fcntl
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path
from threading import Event

import numpy as np
import trimesh

WEIGHTS = (
    "birefnet.gguf",
    "dinov3.gguf",
    "ss_flow.gguf",
    "ss_dec.gguf",
    "shape_flow_512.gguf",
    "shape_dec.gguf",
)


def generate(*args, **kwargs):
    folder = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / f"progretech-visual-{os.getuid()}"
    folder.mkdir(mode=0o700, exist_ok=True)
    with (folder / "rtx.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another visual job owns the GPU. Wait for it to finish.") from None
        return _generate(*args, **kwargs)


def _generate(
    binary: Path,
    weights: Path,
    image: Path,
    job: Path,
    *,
    width_mm: float = 60,
    seed: int = 42,
    cancel: Event | None = None,
    repair: bool = False,
) -> Path:
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError("Select an installed trellis-cli executable.")
    if not all((weights / name).is_file() for name in WEIGHTS):
        raise ValueError("Missing TRELLIS geometry weights. Review the setup requirements.")
    if not np.isfinite(width_mm) or not 5 <= width_mm <= 300:
        raise ValueError("Generated width must be 5–300 mm.")
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**31:
        raise ValueError("Seed must be a nonnegative 31-bit integer.")
    job.mkdir(parents=True, exist_ok=False)
    from seesaw.generation import image_bytes

    normalized = image_bytes(image)
    image = job / "source.png"
    image.write_bytes(normalized)

    def digest(path):
        with path.open("rb") as file:
            return hashlib.file_digest(file, "sha256").hexdigest()

    (job / "provenance.json").write_text(
        json.dumps(
            {
                "image_sha256": hashlib.sha256(normalized).hexdigest(),
                "binary_sha256": digest(binary),
                "weights": {name: digest(weights / name) for name in WEIGHTS},
                "seed": seed,
                "width_mm": width_mm,
                "repair_requested": repair,
            },
            indent=2,
        )
    )
    output = job / "generated.glb"
    post = job / "mesh.post"
    command = [
        str(binary.resolve()),
        str(image.resolve()),
        str(output),
        "--models",
        str(weights.resolve()),
        "--res",
        "512",
        "--no-texture",
        "--steps",
        "12",
        "--seed",
        str(seed),
        "--require-gpu",
        "--sched",
        "off",
        "--dump-post",
        str(post),
    ]
    env = os.environ.copy()
    env.pop("GGML_CUDA_ENABLE_UNIFIED_MEMORY", None)
    env["ROCR_VISIBLE_DEVICES"] = "-1"
    env["HIP_VISIBLE_DEVICES"] = "-1"
    started = time.monotonic()
    peak = 0
    with (job / "runtime.log").open("wb") as log:
        process = subprocess.Popen(
            command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True
        )
        try:
            while process.poll() is None:
                if cancel and cancel.is_set():
                    raise ValueError("Generation cancelled.")
                if time.monotonic() - started > 900:
                    raise ValueError("Generation exceeded the 15-minute limit.")
                probe = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-compute-apps=pid,used_gpu_memory",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if probe.returncode:
                    raise ValueError("CUDA device monitoring failed; generation stopped.")
                used = 0
                for row in probe.stdout.splitlines():
                    pid, memory = row.split(",", 1)
                    if pid.strip() == str(process.pid):
                        used += int(memory.strip())
                peak = max(peak, used)
                if peak >= 12 * 1024:
                    raise ValueError("Generation reached the experimental 12 GiB GPU limit.")
                time.sleep(0.25)
            if process.returncode:
                raise ValueError(
                    "TRELLIS failed; inspect the local runtime.log. CPU relief is available."
                )
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            (job / "runtime.json").write_text(
                json.dumps(
                    {
                        "returncode": process.returncode,
                        "sampled_peak_gpu_mib": peak,
                        "wall_seconds": time.monotonic() - started,
                        "seed": seed,
                        "note": "Sampled memory is not proof against shorter allocation peaks.",
                    },
                    indent=2,
                )
            )
    stl = job / "generated-mm.stl"
    code = (
        "import sys;sys.path.insert(0,sys.argv.pop(1));"
        "from seesaw.trellis import convert_post;convert_post(*sys.argv[1:])"
    )
    with (job / "geometry.log").open("wb") as log:
        converter = subprocess.Popen(
            [
                sys.executable,
                "-c",
                code,
                str(Path(__file__).resolve().parents[1]),
                str(post),
                str(stl),
                str(width_mm),
                str(int(repair)),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        conversion_started = time.monotonic()
        try:
            while converter.poll() is None:
                if cancel and cancel.is_set():
                    raise ValueError("Geometry processing cancelled.")
                if time.monotonic() - conversion_started > 180:
                    raise ValueError("Geometry repair exceeded three minutes.")
                time.sleep(0.1)
            if converter.returncode or not stl.is_file():
                raise ValueError(
                    "Mesh validation failed. Recast or enable repair; see geometry.log."
                )
        finally:
            if converter.poll() is None:
                os.killpg(converter.pid, signal.SIGKILL)
                converter.wait()
    return stl


def convert_post(source_path, destination_path, width, repair):
    post, stl = Path(source_path), Path(destination_path)
    width_mm = float(width)
    if not post.is_file() or post.stat().st_size > 256 * 1024 * 1024:
        raise ValueError("Missing or oversized generated mesh.")
    with post.open("rb") as source:
        header = source.read(16)
        if len(header) != 16:
            raise ValueError("Incomplete native mesh header.")
        vertices, faces, voxels, resolution = struct.unpack("<4i", header)
        if not (
            0 < vertices <= 4_000_000
            and 0 < faces <= 8_000_000
            and voxels == 0
            and resolution == 512
        ):
            raise ValueError("Unsupported native geometry result.")
        if post.stat().st_size != 16 + vertices * 12 + faces * 12:
            raise ValueError("Native mesh length does not match its header.")
        points = np.frombuffer(source.read(vertices * 12), dtype="<f4").reshape((-1, 3))
        triangles = np.frombuffer(source.read(faces * 12), dtype="<i4").reshape((-1, 3))
        if np.any(triangles < 0) or np.any(triangles >= vertices):
            raise ValueError("Native mesh has invalid indices.")
    mesh = trimesh.Trimesh(vertices=points, faces=triangles, process=True)
    original_faces = len(mesh.faces)
    original_bounds = mesh.bounds.copy()
    if not mesh.is_volume and repair == "1":
        import pymeshfix

        points, triangles = pymeshfix.clean_from_arrays(
            mesh.vertices.copy(),
            mesh.faces.astype(np.int32).copy(),
            verbose=False,
            joincomp=False,
            remove_smallest_components=False,
        )
        mesh = trimesh.Trimesh(vertices=points, faces=triangles, process=True)
        if np.max(np.abs(mesh.bounds - original_bounds)) > np.max(mesh.extents) * 0.02:
            raise ValueError("Mesh repair changed outer bounds by more than two percent.")
    if (
        not isinstance(mesh, trimesh.Trimesh)
        or not np.isfinite(mesh.vertices).all()
        or not mesh.is_volume
        or np.any(mesh.extents <= 0)
    ):
        raise ValueError("Generated geometry is not a closed positive solid. Recast or repair it.")
    mesh.apply_scale(width_mm / float(mesh.extents[0]))
    mesh.apply_translation([-mesh.centroid[0], -mesh.centroid[1], -mesh.bounds[0, 2]])
    mesh.export(stl)
    stl.with_suffix(".json").write_text(
        json.dumps(
            {
                "watertight": bool(mesh.is_watertight),
                "positive_volume": bool(mesh.is_volume),
                "repair_requested": repair == "1",
                "input_faces": original_faces,
                "output_faces": len(mesh.faces),
                "dimensions_mm": mesh.extents.tolist(),
                "warning": "Repair may alter fine details. Inspect before slicing.",
            },
            indent=2,
        )
    )
