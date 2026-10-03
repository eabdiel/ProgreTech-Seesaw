"""Verified atomic copy of a validated candidate to a user destination."""

import hashlib
import os
import tempfile
from pathlib import Path


def export_candidate(
    source,
    destination,
    expected_hash,
    cancel=None,
    verify_inputs=lambda: None,
    *,
    extension=".pm4n",
):
    """Copy and verify before atomic publication; never overwrite a source STL."""
    source, destination = Path(source), Path(destination).expanduser().resolve()
    if extension not in {".pm4n", ".gcode"} or destination.suffix.lower() != extension:
        raise ValueError(f"Choose a {extension} destination for the selected printer.")
    if source.resolve() == destination:
        raise ValueError("Choose a destination outside the working candidate.")
    fd, temporary = tempfile.mkstemp(prefix=".seesaw-export-", dir=destination.parent)
    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as target, source.open("rb") as incoming:
            for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
                if cancel is not None and cancel.is_set():
                    raise ValueError("Export cancelled.")
                target.write(chunk)
                digest.update(chunk)
            target.flush()
            os.fsync(target.fileno())
        if digest.hexdigest() != expected_hash:
            raise ValueError("Candidate changed since validation; slice again.")
        # Read the destination filesystem's copy, including USB media, before publishing.
        check = hashlib.sha256()
        with open(temporary, "rb") as target:
            for chunk in iter(lambda: target.read(1024 * 1024), b""):
                check.update(chunk)
        if check.hexdigest() != expected_hash:
            raise ValueError("Export copy verification failed.")
        verify_inputs()
        if cancel is not None and cancel.is_set():
            raise ValueError("Export cancelled.")
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
