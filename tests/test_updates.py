import hashlib
import io
import json
from threading import Event
from urllib.error import URLError

import pytest

from seesaw import updates


def metadata(version="0.2.0", payload=b"deb test bytes"):
    name = f"progretech-seesaw_{version}_amd64.deb"
    return {
        "tag_name": f"v{version}",
        "draft": False,
        "prerelease": False,
        "assets": [
            {
                "name": name,
                "size": len(payload),
                "digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
                "browser_download_url": (
                    f"https://github.com/{updates.REPOSITORY}/releases/download/v{version}/{name}"
                ),
            }
        ],
    }


def test_versions_are_numeric_and_never_downgrade():
    assert updates.parse_release(metadata("0.10.0"), "0.9.0").version == "0.10.0"
    assert updates.parse_release(metadata("0.2.0"), "0.2.0") is None
    assert updates.parse_release(metadata("0.1.0"), "0.2.0") is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("draft", True),
        ("prerelease", True),
        ("tag_name", "v0.2.0;echo bad"),
        ("assets", []),
    ],
)
def test_rejects_unusable_releases(field, value):
    data = metadata()
    data[field] = value
    with pytest.raises(updates.UpdateError):
        updates.parse_release(data, "0.1.0")


@pytest.mark.parametrize(
    "field,value",
    [
        ("digest", None),
        ("digest", "sha256:bad"),
        ("size", -1),
        ("size", updates.MAX_PACKAGE + 1),
        ("browser_download_url", "https://example.org/installer.deb"),
    ],
)
def test_rejects_unverifiable_asset(field, value):
    data = metadata()
    data["assets"][0][field] = value
    with pytest.raises(updates.UpdateError):
        updates.parse_release(data, "0.1.0")


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/file",
        "file:///tmp/installer",
        "https://evil.com/file",
        "https://github.com@evil.com/file",
        "https://github.com:123/file",
    ],
)
def test_rejects_redirects_outside_github_https(url):
    with pytest.raises(updates.UpdateError):
        updates.validate_url(url)


def test_offline_check_has_actionable_error(monkeypatch):
    def offline(_):
        raise URLError("network unavailable")

    monkeypatch.setattr(updates, "open_url", offline)
    with pytest.raises(updates.UpdateError, match="connection"):
        updates.check_latest("0.1.0")


def test_check_parses_realistic_api_response(monkeypatch):
    monkeypatch.setattr(updates, "open_url", lambda _: io.BytesIO(json.dumps(metadata()).encode()))
    assert updates.check_latest("0.1.0").version == "0.2.0"


def test_download_verifies_bytes_before_publishing(monkeypatch, tmp_path):
    payload = b"a package with some bytes"
    release = updates.parse_release(metadata(payload=payload), "0.1.0")
    monkeypatch.setattr(updates, "open_url", lambda _: io.BytesIO(payload))
    path = updates.download_release(release, tmp_path, Event())
    assert path.read_bytes() == payload
    assert not path.with_name("download.part").exists()


@pytest.mark.parametrize("body", [b"", b"wrong checksum", b"x" * 100])
def test_failed_download_leaves_no_candidate(monkeypatch, tmp_path, body):
    release = updates.parse_release(metadata(), "0.1.0")
    monkeypatch.setattr(updates, "open_url", lambda _: io.BytesIO(body))
    with pytest.raises(updates.UpdateError):
        updates.download_release(release, tmp_path, Event())
    assert list(tmp_path.iterdir()) == []


def test_cancel_cleans_partial_download(monkeypatch, tmp_path):
    release = updates.parse_release(metadata(), "0.1.0")
    monkeypatch.setattr(updates, "open_url", lambda _: io.BytesIO(b"deb test bytes"))
    event = Event()
    event.set()
    with pytest.raises(updates.Cancelled):
        updates.download_release(release, tmp_path, event)
    assert list(tmp_path.iterdir()) == []
