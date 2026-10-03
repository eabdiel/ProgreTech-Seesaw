import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from PIL import Image

from seesaw.generation import ReliefSettings, chat, create_relief, endpoint_url
from seesaw.model import load_stl


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "http://machine.ts.net",
        "http://127.0.0.1@evil.com",
        "https://machine.ts.net/?token=secret",
        "https://machine.ts.net/evil",
        "file:///tmp/test",
    ],
)
def test_connection_rejects_untrusted_transport(url):
    with pytest.raises(ValueError):
        endpoint_url(url)


def test_relief_closed_scaled_and_no_overwrite(tmp_path):
    source = tmp_path / "source.png"
    Image.linear_gradient("L").resize((40, 20)).save(source)
    output = tmp_path / "relief.stl"
    result = create_relief(source, output, ReliefSettings(60, 2, 3))
    mesh, info = load_stl(output)
    assert mesh.is_volume and info.watertight
    assert info.dimensions_mm[0] == pytest.approx(60)
    assert mesh.bounds[0, 2] == 0
    assert 2 < info.dimensions_mm[2] <= 5
    assert result["mode"] == "image-relief"
    with pytest.raises(FileExistsError):
        create_relief(source, output, ReliefSettings())


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True])
def test_invalid_relief_settings(value):
    with pytest.raises(ValueError):
        ReliefSettings(width_mm=value)


def test_chat_image_session_and_redirect_refusal(tmp_path):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            if len(requests) == 2:
                self.send_response(302)
                self.send_header("Location", "http://localhost:1/leak")
                self.end_headers()
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                json.dumps({"choices": [{"message": {"content": "Local reply"}}]}).encode()
            )

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    source = tmp_path / "image.png"
    Image.new("RGB", (10, 10)).save(source)
    endpoint = f"http://127.0.0.1:{server.server_port}"
    try:
        assert (
            chat(endpoint, "test-only", "imagen", "thread1", "Make relief", source) == "Local reply"
        )
        assert requests[0]["model"] == "openclaw/imagen"
        assert requests[0]["user"] == "seesaw-thread1"
        assert requests[0]["messages"][0]["content"][1]["image_url"]["url"].startswith(
            "data:image/png;"
        )
        with pytest.raises(ValueError, match="redirect"):
            chat(endpoint, "test-only", "imagen", "thread1", "Recast")
    finally:
        server.shutdown()
        server.server_close()


def test_native_mesh_header_rejects_oversized_counts(tmp_path):
    import struct

    from seesaw.trellis import convert_post

    source = tmp_path / "mesh.post"
    source.write_bytes(struct.pack("<4i", 5_000_000, 1, 0, 512))
    with pytest.raises(ValueError, match="Unsupported"):
        convert_post(str(source), str(tmp_path / "out.stl"), "60", "0")
    assert not (tmp_path / "out.stl").exists()


def test_native_mesh_conversion_preserves_solid_and_explicit_size(tmp_path):
    import struct

    import numpy as np
    import trimesh

    from seesaw.trellis import convert_post

    mesh = trimesh.creation.box((1, 2, 3))
    source = tmp_path / "mesh.post"
    source.write_bytes(
        struct.pack("<4i", len(mesh.vertices), len(mesh.faces), 0, 512)
        + mesh.vertices.astype("<f4").tobytes()
        + mesh.faces.astype("<i4").tobytes()
    )
    output = tmp_path / "out.stl"
    convert_post(str(source), str(output), "60", "0")
    converted, info = load_stl(output)
    assert converted.is_volume
    assert np.allclose(info.dimensions_mm, [60, 120, 180])
    assert converted.bounds[0, 2] == 0
