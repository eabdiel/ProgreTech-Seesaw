"""Bounded one-layer thumbnail reads from the validated native-file readback."""

import io
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from seesaw.model import MONO4


class LayerPreview:
    def __init__(self, archive: Path, expected_count: int, focus=None):
        self.archive = Path(archive)
        self.focus = focus
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
                picture = picture.convert("L")
                if self.focus is not None and self.focus.layer == index:
                    f = self.focus
                    left, top = max(0, f.x - 64), max(0, f.y - 64)
                    right, bottom = min(9024, f.x + f.width + 64), min(5120, f.y + f.height + 64)
                    picture = picture.crop((left, top, right, bottom)).convert("RGB")
                    draw = ImageDraw.Draw(picture)
                    draw.rectangle(
                        (
                            f.x - left - 2,
                            f.y - top - 2,
                            f.x - left + f.width + 1,
                            f.y - top + f.height + 1,
                        ),
                        outline="#ef5350",
                        width=1,
                    )
                    scale = min(900 / picture.width, 512 / picture.height)
                    picture = picture.resize(
                        (
                            max(1, round(picture.width * scale)),
                            max(1, round(picture.height * scale)),
                        ),
                        Image.Resampling.NEAREST,
                    )
                picture.thumbnail((900, 512))
                result = io.BytesIO()
                picture.save(result, format="PNG")
                return result.getvalue()
