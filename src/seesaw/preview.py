"""Bounded one-layer thumbnail reads from the validated native-file readback."""

import io
import re
import zipfile
from pathlib import Path

from PIL import Image

from seesaw.model import MONO4


class LayerPreview:
    def __init__(self, archive: Path, expected_count: int):
        self.archive = Path(archive)
        with zipfile.ZipFile(self.archive) as source:
            if len(source.infolist()) > 1024:
                raise ValueError("Too many archive entries.")
            self.names = sorted(
                entry.filename
                for entry in source.infolist()
                if re.fullmatch(r"[^/]+\d{5}\.png", entry.filename)
            )
            if (
                not 1 <= expected_count <= 512
                or len(self.names) != expected_count
                or len(set(self.names)) != expected_count
            ):
                raise ValueError("Preview layer count does not match the validated job.")

    def thumbnail(self, index: int) -> bytes:
        if type(index) is not int or not 0 <= index < len(self.names):
            raise ValueError("Layer index is out of range.")
        with zipfile.ZipFile(self.archive) as source:
            entry = source.getinfo(self.names[index])
            if entry.file_size > 100 * 1024**2:
                raise ValueError("Layer PNG exceeds its size limit.")
            with source.open(entry) as stream, Image.open(stream) as picture:
                if picture.size != MONO4.resolution_px:
                    raise ValueError("Unexpected layer raster dimensions.")
                picture.thumbnail((900, 512))
                result = io.BytesIO()
                picture.convert("L").save(result, format="PNG")
                return result.getvalue()
