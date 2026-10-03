"""Optional generation boundaries. No network or model loading during normal slicing."""

import base64
import io
import ipaddress
import json
import math
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from threading import Event

import numpy as np
import trimesh
from PIL import Image, ImageOps

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_REPLY_BYTES = 1024 * 1024


def endpoint_url(value: str) -> str:
    """Private transport only; never forward a gateway token through redirects/proxies."""
    parsed = urllib.parse.urlsplit(value.strip())
    host = parsed.hostname or ""
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not (loopback or (parsed.scheme == "https" and host.endswith(".ts.net"))):
        raise ValueError("Use loopback on this computer or your HTTPS Tailscale .ts.net address.")
    if (
        parsed.scheme not in {"http", "https"}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/", "/v1"}
    ):
        raise ValueError("Enter the gateway base address without credentials, query or API path.")
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError("Invalid gateway port.") from exc
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Gateway redirects are refused; enter the final private address.")


def image_bytes(path: Path) -> bytes:
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("Choose an image smaller than 8 MiB.")
    with Image.open(path) as source:
        if source.width * source.height > 24_000_000:
            raise ValueError("Image exceeds 24 megapixels.")
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1536, 1536))
        output = io.BytesIO()
        image.save(output, format="PNG")
    data = output.getvalue()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Normalized image exceeds 8 MiB.")
    return data


@dataclass(frozen=True)
class ReliefSettings:
    width_mm: float = 60
    base_mm: float = 2
    depth_mm: float = 3
    invert: bool = False

    def __post_init__(self):
        for key, low, high in (("width_mm", 5, 300), ("base_mm", 0.5, 20), ("depth_mm", 0.1, 30)):
            value = getattr(self, key)
            if isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{key} must be between {low} and {high}.")
        if not isinstance(self.invert, bool):
            raise ValueError("invert must be a boolean.")


def create_relief(source: Path, destination: Path, settings: ReliefSettings) -> dict:
    """A closed height field with a flat base; this does not infer hidden object geometry."""
    with Image.open(io.BytesIO(image_bytes(source))) as original:
        image = ImageOps.grayscale(original)
        image.thumbnail((192, 192))
        if min(image.size) < 2:
            raise ValueError("Image needs at least two pixels on each axis.")
        pixels = np.asarray(image, dtype=float)[::-1] / 255
    if settings.invert:
        pixels = 1 - pixels
    rows, cols = pixels.shape
    height = settings.width_mm * (rows - 1) / (cols - 1)
    x, y = np.meshgrid(np.linspace(0, settings.width_mm, cols), np.linspace(0, height, rows))
    vertices = np.column_stack(
        (x.ravel(), y.ravel(), (settings.base_mm + pixels * settings.depth_mm).ravel())
    )
    count = len(vertices)
    bottom = vertices.copy()
    bottom[:, 2] = 0
    vertices = np.vstack((vertices, bottom))
    faces = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            a = r * cols + c
            b, d, e = a + 1, a + cols, a + cols + 1
            faces.extend(
                (
                    (a, b, e),
                    (a, e, d),
                    (a + count, e + count, b + count),
                    (a + count, d + count, e + count),
                )
            )
    boundary = (
        list(range(cols))
        + [r * cols + cols - 1 for r in range(1, rows)]
        + list(range((rows - 1) * cols + cols - 2, (rows - 1) * cols - 1, -1))
        + [r * cols for r in range(rows - 2, 0, -1)]
    )
    for a, b in zip(boundary, boundary[1:] + boundary[:1], strict=True):
        faces.extend(((a, a + count, b + count), (a, b + count, b)))
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    if not mesh.is_volume or not mesh.is_watertight:
        raise ValueError("Generated relief failed closed-volume validation.")
    # Caller supplies a fresh job filename; never overwrite an existing model.
    with destination.open("xb") as target:
        target.write(mesh.export(file_type="stl"))
    return {
        "mode": "image-relief",
        "watertight": True,
        "dimensions_mm": mesh.extents.tolist(),
        "triangles": len(mesh.faces),
    }


def chat(
    base: str,
    token: str,
    agent: str,
    session: str,
    prompt: str,
    image: Path | None = None,
    model_override: str | None = None,
) -> str:
    base = endpoint_url(base)
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", agent):
        raise ValueError("Invalid OpenClaw agent ID.")
    if not token.strip() or any(c in token for c in "\r\n"):
        raise ValueError("Enter the gateway token; it is kept only in memory.")
    if not prompt.strip() or len(prompt) > 16000:
        raise ValueError("Enter a prompt of at most 16,000 characters.")
    content = [{"type": "text", "text": prompt}]
    if image:
        encoded = base64.b64encode(image_bytes(image)).decode("ascii")
        content.append(
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + encoded}}
        )
    body = {
        "model": "openclaw/" + agent,
        "user": "seesaw-" + session,
        "stream": False,
        "messages": [{"role": "user", "content": content}],
    }
    request = urllib.request.Request(
        base + "/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    if model_override:
        if not re.fullmatch(r"ollama/[a-zA-Z0-9_.:/-]{1,100}", model_override):
            raise ValueError("Only explicit local Ollama model overrides are supported.")
        request.add_header("x-openclaw-model", model_override)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=600) as response:
            raw = response.read(MAX_REPLY_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise ValueError(
            f"Gateway returned HTTP {exc.code}. Check endpoint, agent and token."
        ) from None
    except urllib.error.URLError:
        raise ValueError(
            "Cannot reach gateway. Check OpenClaw and the Tailscale connection."
        ) from None
    if len(raw) > MAX_REPLY_BYTES:
        raise ValueError("Gateway response exceeds 1 MiB.")
    try:
        result = json.loads(raw)["choices"][0]["message"]["content"]
        if not isinstance(result, str) or not result.strip():
            raise ValueError
        return result
    except (KeyError, IndexError, TypeError, ValueError):
        raise ValueError("Gateway did not return a text response.") from None


def cancellable_chat(arguments: dict, cancel: Event) -> str:
    """Keep the credential in a pipe, and stop waiting without blocking Qt shutdown."""
    code = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from pathlib import Path;from seesaw.generation import chat;"
        "d=json.load(sys.stdin);d['image']=Path(d['image']) if d.get('image') else None;"
        "print(json.dumps({'reply':chat(**d)}))"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(Path(__file__).resolve().parents[1])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    payload = json.dumps(arguments)
    try:
        while True:
            if cancel.is_set():
                raise ValueError("Stopped waiting for the agent. Remote work may continue.")
            try:
                output, _ = process.communicate(input=payload, timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                payload = None
        if process.returncode:
            raise ValueError(
                "Agent request failed or timed out. Check the connection and agent logs."
            )
        return json.loads(output)["reply"]
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
